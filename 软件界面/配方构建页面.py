from pathlib import Path

import pandas as pd
import streamlit as st

from 核心系统.化合物确认清单 import 已确认清单目录, 读取确认清单
from 核心系统.数据管理接口 import 文件数据访问管理器
from 核心系统.颅骨透明化用途 import 保存HSP参照, 保存配方设置, 读取HSP参照, 读取成分证据, 读取配方设置, 运行用途评估, 读取确认批次描述符
from 插件.颅骨透明化.颅骨透明化用途插件 import 用途标识


项目根目录 = Path(__file__).resolve().parents[1]


def 渲染配方构建页面() -> None:
    st.header("配方构建")
    if not hasattr(st, "selectbox"):  # 保持最小页面接口在无 Streamlit 环境可测试。
        st.info("颅骨透明化配方数据录入与用途评估入口。")
        return
    管理器 = 文件数据访问管理器(项目根目录)
    目录 = 已确认清单目录(管理器)
    目录 = 目录.loc[目录.get("用途标识", pd.Series(dtype=str)).astype(str).eq(用途标识)] if not 目录.empty and "用途标识" in 目录 else pd.DataFrame()
    if 目录.empty:
        st.info("尚无已确认的颅骨透明化批次。请先在“用户候选导入”确认完整化合物清单。")
        return
    显示 = {f"{行['批次编号']}｜{行.get('清单名称', '')}": str(行["批次编号"]) for _, 行 in 目录.iterrows()}
    批次编号 = st.selectbox("选择颅骨透明化批次", list(显示.values()), format_func=lambda 值: next(标签 for 标签, 编号 in 显示.items() if 编号 == 值))
    元数据, 清单 = 读取确认清单(管理器, 批次编号)
    st.caption(f"目标 RI：{元数据.get('目标折射率', 1.56)}；用途配置版本：{元数据.get('用途配置版本', '1.0')}。成分数据来自已确认工作清单，此页不要求重新录入。")

    成分证据 = 读取成分证据(管理器, 批次编号, 清单)
    st.subheader("已确认的成分与颅骨专用字段")
    st.dataframe(成分证据, use_container_width=True, hide_index=True)
    描述符 = 读取确认批次描述符(管理器, 批次编号)
    st.caption(f"确认后已生成 {len(描述符)} 条通用化学描述符；配方评估会自动将其与此清单聚合。")

    st.subheader("HSP 参照体系")
    HSP参照 = 读取HSP参照(管理器, 批次编号)
    if HSP参照.empty:
        HSP参照 = pd.DataFrame([{"参照体系": "AqIS", "HSP_dD": pd.NA, "HSP_dP": pd.NA, "HSP_dH": pd.NA, "数据来源": ""}, {"参照体系": "oRIMS", "HSP_dD": pd.NA, "HSP_dP": pd.NA, "HSP_dH": pd.NA, "数据来源": ""}])
    HSP编辑后 = st.data_editor(HSP参照.drop(columns=["批次编号"], errors="ignore"), num_rows="dynamic", use_container_width=True, hide_index=True, key=f"HSP参照_{批次编号}")
    if st.button("保存 HSP 参照", key=f"保存HSP_{批次编号}"):
        保存HSP参照(管理器, 批次编号, HSP编辑后)
        st.success("已保存 HSP 参照；仅在候选和参照的 dD/dP/dH 均完整时计算 Ra。")

    st.subheader("配方层实验/观察数据")
    设置 = 读取配方设置(管理器, 批次编号)
    左, 中, 右 = st.columns(3)
    混合RI = 左.text_input("混合液实测 RI", value=str(设置.get("混合液实测RI", "")), key=f"混合RI_{批次编号}")
    混溶 = 中.text_input("实验混溶性", value=str(设置.get("实验混溶性", "")), key=f"混溶_{批次编号}")
    稳定性 = 右.text_input("稳定性状态", value=str(设置.get("稳定性状态", "")), key=f"稳定性_{批次编号}")
    水相分离 = st.text_input("水触发相分离", value=str(设置.get("水触发相分离", "")), key=f"水相分离_{批次编号}")
    if st.button("保存配方层数据", key=f"保存配方_{批次编号}"):
        保存配方设置(管理器, 批次编号, {"混合液实测RI": 混合RI, "实验混溶性": 混溶, "稳定性状态": 稳定性, "水触发相分离": 水相分离})
        st.success("已保存配方层观察数据。")

    if st.button("运行颅骨透明化用途评估", type="primary", key=f"评估_{批次编号}"):
        结果 = 运行用途评估(管理器, 批次编号, 清单, {键: 元数据.get(键) for 键 in ("用途标识", "用途名称", "用途配置版本", "目标折射率", "温度_C", "HSP参照体系")})
        st.success("用途评估完成；缺失字段会显示为待补，不会生成虚构预测。")
        st.dataframe(结果["配方摘要"], use_container_width=True, hide_index=True)
        if not 结果["组分HSP结果"].empty:
            st.caption("多化合物组分两两 HSP 距离：用于识别配方内部的相容性风险，不替代实验混溶性。")
            st.dataframe(结果["组分HSP结果"], use_container_width=True, hide_index=True)
        st.dataframe(结果["配方特征"], use_container_width=True, hide_index=True)
