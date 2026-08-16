"""读取已匹配的PubChem身份，并保存GHS危险提示为独立毒性证据。"""

from datetime import datetime, timezone
import json
import re
from typing import Any
from urllib.parse import quote

import pandas as pd
import requests

from 插件.插件接口 import 基础插件接口


class PubChem查询插件(基础插件接口):
    插件标识 = "PubChem查询"
    输出标识 = "PubChem_GHS毒性证据"
    缓存文件 = "PubChem_GHS缓存.csv"
    毒理公开输出标识 = "毒理公开证据_PubChemGHS"
    毒理公开日志标识 = "毒理公开查询日志"
    毒理公开原始响应标识 = "毒理公开原始响应_PubChemGHS"

    @staticmethod
    def _提取文本(对象: Any) -> list[str]:
        if isinstance(对象, dict):
            输出 = []
            for 键, 值 in 对象.items():
                if 键 in {"String", "Description", "Name"} and isinstance(值, str):
                    输出.append(值)
                输出.extend(PubChem查询插件._提取文本(值))
            return 输出
        if isinstance(对象, list):
            return [文本 for 值 in 对象 for 文本 in PubChem查询插件._提取文本(值)]
        return []

    def _GHS(self, CID: str) -> tuple[dict[str, str], str]:
        地址 = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{CID}/JSON?heading=GHS%20Classification"
        响应 = requests.get(地址, timeout=20)
        if 响应.status_code == 404:
            return {}, "未找到GHS条目"
        响应.raise_for_status()
        原始 = 响应.json()
        文本 = self._提取文本(原始)
        # 只识别形如 H300/H314 的正式危险代码；说明文字、ECHA介绍等不会误入。
        代码 = sorted({值 for 片段 in 文本 for 值 in re.findall(r"\bH\d{3}\b", 片段)})
        说明 = [片段 for 片段 in 文本 if re.search(r"\bH\d{3}\b", 片段)]
        信号词 = sorted({值 for 片段 in 文本 for 值 in re.findall(r"\b(?:Danger|Warning)\b", 片段, flags=re.I)})
        类别 = [片段 for 片段 in 文本 if re.search(r"(?:Acute Toxicity|Skin Corrosion|Eye Damage|Carcinogenicity|Reproductive Toxicity|Specific Target Organ|Flammable)", 片段, flags=re.I)]
        比例 = sorted({值 for 片段 in 文本 for 值 in re.findall(r"\b\d+(?:\.\d+)?%", 片段)})
        来源 = sorted({片段 for 片段 in 文本 if re.search(r"(?:ECHA|EPA|European Chemicals Agency|submission|notifier)", 片段, flags=re.I)})
        return {"H代码": "; ".join(代码), "危险说明": " | ".join(dict.fromkeys(说明))[:3000], "信号词": "; ".join(信号词), "危险类别": " | ".join(dict.fromkeys(类别))[:2000], "报告比例": "; ".join(比例), "提交来源": " | ".join(dict.fromkeys(来源))[:1500], "是否存在不同来源冲突": "是" if len(代码) > 1 else "未见明确冲突", "原始响应": json.dumps(原始, ensure_ascii=False)}, ""

    @staticmethod
    def _查询CID(查询值: str) -> tuple[str, str]:
        """用 CAS 或名称解析唯一 CID；多结果时不擅自选择。"""
        if not 查询值.strip():
            return "", "没有可用于 PubChem 查询的 CID、CAS 或化学名称"
        地址 = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(查询值.strip(), safe='')}/cids/JSON"
        响应 = requests.get(地址, timeout=20)
        if 响应.status_code == 404:
            return "", f"PubChem 未找到：{查询值}"
        响应.raise_for_status()
        CID列表 = [str(值) for 值 in 响应.json().get("IdentifierList", {}).get("CID", [])]
        if len(CID列表) != 1:
            return "", "PubChem 返回多个 CID，未自动选择" if CID列表 else f"PubChem 未找到：{查询值}"
        return CID列表[0], ""

    @staticmethod
    def _缓存索引(缓存: pd.DataFrame) -> dict[str, dict[str, Any]]:
        return {str(行.get("PubChem CID", "")): 行.to_dict() for _, 行 in 缓存.iterrows() if str(行.get("PubChem CID", ""))} if not 缓存.empty else {}

    def _执行毒理公开查询(self, 数据上下文: dict[str, Any]) -> pd.DataFrame:
        """查询确认批次中的 PubChem GHS，并输出不可匹配的危险提示证据。"""
        数据管理器 = 数据上下文["数据管理器"]
        原始候选 = 数据上下文.get("公开毒理候选")
        候选 = 原始候选.copy() if isinstance(原始候选, pd.DataFrame) else pd.DataFrame(原始候选 or [])
        if 候选.empty:
            return pd.DataFrame()
        使用缓存 = bool(数据上下文.get("允许使用缓存", True))
        try:
            缓存 = 数据管理器.读取软件数据库表格(self.缓存文件)
        except FileNotFoundError:
            缓存 = pd.DataFrame()
        缓存索引 = self._缓存索引(缓存)
        证据记录, 日志记录, 原始响应记录 = [], [], []
        for _, 行 in 候选.iterrows():
            候选编号 = str(行.get("候选编号", ""))
            CID = str(行.get("PubChem CID", "") or "").strip()
            查询方式, 错误, 结构化结果, 缓存命中 = ("确认清单 PubChem CID", "", {}, False)
            if not CID:
                for 字段, 名称 in (("CAS", "CAS"), ("CAS号", "CAS"), ("化学名称", "化学名称")):
                    查询值 = str(行.get(字段, "") or "").strip()
                    if 查询值:
                        查询方式 = 名称
                        try:
                            CID, 错误 = self._查询CID(查询值)
                        except requests.RequestException as 异常:
                            错误 = f"CID 查询失败：{type(异常).__name__}: {异常}"
                        break
            缓存值 = 缓存索引.get(CID) if CID and 使用缓存 else None
            if 缓存值:
                缓存命中 = True
                结构化结果 = {键: str(缓存值.get(键, "")) for 键 in ("H代码", "危险说明", "信号词", "危险类别", "报告比例", "提交来源", "是否存在不同来源冲突", "原始响应")}
                错误 = str(缓存值.get("查询错误", ""))
            elif CID and not 错误:
                try:
                    结构化结果, 错误 = self._GHS(CID)
                except requests.RequestException as 异常:
                    错误 = f"GHS 查询失败：{type(异常).__name__}: {异常}"
                except (ValueError, KeyError) as 异常:
                    错误 = f"GHS 响应解析失败：{type(异常).__name__}: {异常}"
            查询时间 = datetime.now(timezone.utc).isoformat()
            查询状态 = "已查询" if bool(结构化结果.get("H代码") or 结构化结果.get("危险说明")) else ("无GHS结果" if CID and not 错误 else "查询失败")
            缓存记录 = {"PubChem CID": CID, **结构化结果, "查询错误": 错误, "查询时间": 查询时间}
            if CID and 使用缓存:
                缓存索引[CID] = 缓存记录
            批次字段 = {键: str(行.get(键, "")) for 键 in ("批次编号", "来源运行编号", "确认清单标识")}
            证据记录.append({
                **批次字段, "候选编号": 候选编号, "化学名称": str(行.get("化学名称", "")), "CAS": str(行.get("CAS", 行.get("CAS号", "")) or ""),
                "PubChem CID": CID, "InChIKey": str(行.get("InChIKey", "")), "证据来源类型": "公开数据", "公开数据源": "PubChem GHS",
                "证据分类": "危险提示", "证据可参与条件匹配": False, "毒性终点": "GHS危险提示", "物种": "不适用", "给药途径": "不适用",
                "结果": 结构化结果.get("危险说明", "") or 错误, "实验值或预测值": "数据库汇总", "原始数据、数据库汇总或模型预测": "数据库汇总",
                "数据来源": "PubChem PUG-View GHS Classification", "原始来源链接或编号": f"https://pubchem.ncbi.nlm.nih.gov/compound/{CID}" if CID else "",
                "可信度": "公开 GHS 危险提示；不等同于实验毒理结论", "数据是否与当前实验条件匹配": "否/不适用", "备注": "不参与 A/B/C/D 条件匹配或自动淘汰", "查询方式": 查询方式,
                "查询状态": 查询状态, "缓存命中": "是" if 缓存命中 else "否", **结构化结果,
            })
            日志记录.append({**批次字段, "候选编号": 候选编号, "公开数据源": "PubChem GHS", "PubChem CID": CID, "查询方式": 查询方式, "查询状态": 查询状态, "缓存命中": "是" if 缓存命中 else "否", "查询时间": 查询时间, "错误": 错误})
            if 结构化结果.get("原始响应"):
                原始响应记录.append({**批次字段, "候选编号": 候选编号, "公开数据源": "PubChem GHS", "PubChem CID": CID, "查询时间": 查询时间, "原始响应": 结构化结果["原始响应"]})
        if 使用缓存:
            数据管理器.保存软件数据库表格(self.缓存文件, pd.DataFrame(缓存索引.values()))
        证据 = pd.DataFrame(证据记录)
        数据管理器.保存筛选结果(self.毒理公开输出标识, 证据)
        数据管理器.保存筛选结果(self.毒理公开日志标识, pd.DataFrame(日志记录))
        数据管理器.保存筛选结果(self.毒理公开原始响应标识, pd.DataFrame(原始响应记录))
        return 证据

    def 执行(self, 数据上下文: dict[str, Any]) -> pd.DataFrame:
        if "公开毒理候选" in 数据上下文:
            return self._执行毒理公开查询(数据上下文)
        数据管理器 = 数据上下文["数据管理器"]
        身份 = 数据管理器.读取中间结果("补充数据2_41候选身份映射")
        筛选 = 数据管理器.读取筛选结果("补充数据2_规则筛选统一记录")
        最终 = 筛选[筛选["自动规则通过"].astype(str).str.lower().eq("true")][["候选编号", "论文_CAS号"]]
        表 = 最终.merge(身份, on="候选编号", how="left", suffixes=("", "_身份"))
        try:
            缓存 = 数据管理器.读取软件数据库表格(self.缓存文件)
        except FileNotFoundError:
            缓存 = pd.DataFrame(columns=["PubChem CID", "GHS结果", "查询错误", "查询时间"])
        缓存索引 = {str(行["PubChem CID"]): 行.to_dict() for _, 行 in 缓存.iterrows()} if not 缓存.empty else {}
        记录 = []
        for _, 行 in 表.iterrows():
            结构化结果, 错误 = {}, ""
            CID = str(行.get("PubChem CID", ""))
            缓存值 = 缓存索引.get(CID)
            if 缓存值:
                结构化结果 = {键: str(缓存值.get(键, "")) for 键 in ["H代码", "危险说明", "信号词", "危险类别", "报告比例", "提交来源", "是否存在不同来源冲突", "原始响应"]}
                错误 = str(缓存值.get("查询错误", ""))
            elif 数据上下文.get("启用网络毒性查询") and CID:
                try:
                    结构化结果, 错误 = self._GHS(CID)
                except Exception as 异常:
                    错误 = f"查询失败：{type(异常).__name__}: {异常}"
            else:
                错误 = "本次未执行网络查询；GHS仅作危险提示，不等同于实验风险"
            缓存索引[CID] = {"PubChem CID": CID, **结构化结果, "查询错误": 错误, "查询时间": datetime.now(timezone.utc).isoformat()}
            记录.append({"候选编号": 行["候选编号"], "CAS": 行.get("论文_CAS号", 行.get("原始CAS", "")), "PubChem CID": CID, "InChIKey": 行.get("InChIKey", ""), "化合物形式": "盐/水合物/混合物状态见身份映射", "毒性终点": "GHS危险提示", "物种": "不适用", "细胞或组织来源": "不适用", "给药途径": "不适用", "剂量": "", "剂量单位": "", "暴露时长": "", "观察时长": "", "结果": 结构化结果.get("危险说明", "") or 错误, "实验值或预测值": "数据库汇总", "原始数据、数据库汇总或模型预测": "数据库汇总", "数据来源": "PubChem PUG-View GHS Classification", "原始来源链接或编号": f"https://pubchem.ncbi.nlm.nih.gov/compound/{CID}" if CID else "", "可信度": "GHS危险提示；需追溯原始来源", "数据是否与当前实验条件匹配": "否/不适用", "备注": "GHS不自动作为实验风险或淘汰规则", "查询状态": "已查询" if bool(结构化结果.get("H代码") or 结构化结果.get("危险说明")) else "尚未查询或无结果", **结构化结果})
        证据 = pd.DataFrame(记录)
        数据管理器.保存软件数据库表格(self.缓存文件, pd.DataFrame(缓存索引.values()))
        数据管理器.保存中间结果(self.输出标识, 证据)
        return 证据
