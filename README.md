# Amadeus: Automated Screening Framework

**Demo 2.0**｜颅骨透明化试剂候选筛选研究原型

Amadeus 将 SeeThrough 论文补充数据中的候选物，经可配置数值规则、RDKit 结构处理和 Hansen 溶解度参数距离计算，形成可追溯的候选筛选结果、交互式结果视图和可下载报告。

> 研究原型，不用于直接证明安全性、透明化效果或临床适用性。

## 现在能做什么

- **论文复现筛选**：读取 SeeThrough 补充数据 2，按必要字段、水合评分、水合能力、eRI 和与 BA 的 Hansen 距离逐步筛选；每一步均保留候选数量和逐候选审计记录。
- **用户候选筛选**：导入 CSV/XLSX，映射字段，选择水相、有机相、通用或自定义应用配置，并按本轮 `run_id` 隔离输入、结果与报告。
- **化学信息处理**：执行身份映射与冲突记录、RDKit 结构/描述符计算，以及与 BA/VA 的 Hansen 距离计算；身份冲突可在独立页面审核。
- **结果与报告**：查看 20 个自动候选及其筛选过程，下载 Excel 报告、300 DPI PNG 和 SVG；规则筛选页还提供可悬停、缩放的流程与候选散点图。
- **证据与实验工作流**：查看毒性/GHS 证据与数据缺口，基于已确认批次进行配方构建和实验记录；这些页面不生成安全性或透明化效果结论。

当前 SeeThrough 水相候选演示计算链为 **1619 → 1373 → 1297 → 225 → 41 → 20**；自动规则获得 20 个候选，论文最终 10 个候选在自动候选中恢复 **10/10**。

## Demo 1.0 与 2.0 对比

与 [SeeThrough 参考演示 1.0](https://github.com/sakana-enthusiasts/automatic-screening-framework_SeeThrough_demo_1.0) 使用同一套论文数据和筛选链；下表同时列出目前各模块的接入状态与验证情况。

| 部分 | 原版 1.0 | 现在新版本 | 差别 |
| --- | --- | --- | --- |
| 论文公开数据筛选（已验证） | 已有，按论文数据、规则和 HSP 流程筛选 | 保留原计算链，并扩展为可处理用户候选集 | 保留论文筛选；增加用户候选处理 |
| 用户候选的大批量初筛（已接入） | 有导入与规则入口，但用户数据的 HSP 链路不完整 | 导入后自动计算 BA/VA HSP 距离，再执行应用规则 | 补全 HSP 计算与规则链路 |
| 化合物工作清单（已接入） | 基本是一轮导入、一轮筛选 | 唯一工作清单；可多轮加入候选，记录浓度、角色和最终确认批次 | 新增工作清单与确认批次 |
| 历史与可追溯性（已接入） | 以页面入口为主 | 最终清单冻结为批次；描述符、HSP、用途评估和实验记录按批次保存 | 新增批次记录 |
| 颅骨透明化专用能力（已接入） | 有配方、实验、预测页面的雏形 | 颅骨用途插件，RI/eRI、水合、HSP、溶解/混溶/颜色/pH/组织作用字段，确认后自动汇总 | 新增用途字段与汇总 |
| 多化合物配方（已接入） | 更偏候选筛选 | 支持同一配方清单下的角色、浓度、组分两两 HSP 和配方特征汇总 | 新增多组分配方计算 |
| 毒理与公开数据（部分接入） | 偏证据展示和预留接口 | 已接 PubChem GHS 证据，并可与确认批次、毒理匹配记录关联 | 接入 PubChem GHS 证据 |
| 预测模型（GP/贝叶斯等，预留） | 预留接口 | 仍是预留接口；没有训练完成、可可靠调用的模型 | 仍为预留接口 |
| 实验优化（预留） | 入口/框架 | 仍未形成真正闭环优化 | 仍为预留框架 |

## 安装与启动

建议使用 Python 3.11 或与 RDKit 兼容的 Python 环境。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run 启动程序.py
```

浏览器打开的本地页面中，选择“规则筛选”并点击“重新运行完整筛选”，即可生成当前数据的报告和图表。

公开 Demo 不包含测试与本地审计代码。安装后可先进行基础语法检查：

```powershell
python -m compileall 核心系统 插件 软件界面 设置
```

本地演示不需要 API 密钥。可选在线毒性查询如需密钥，只能置于本机环境变量；不要提交 `.env`、令牌或私人导入表格。

## 本地交互式结果可视化

Demo 默认启用结果可视化。核心计算与展示层相互独立：关闭图表不会影响筛选、报告导出或结果保存。

开发新规则或调整输出字段时，可以临时关闭：

```powershell
$env:AMADEUS_ENABLE_RESULT_VISUALIZATION = "0"
streamlit run 启动程序.py
```

重新打开 PowerShell 或设置为 `1` 后，图表会恢复。该开关适合在核心逻辑尚未稳定时避免界面兼容性干扰开发。

## 已知边界

- 本项目不是经过前瞻性实验验证的透明化效果预测系统；
- 毒性信息目前作为可追溯证据与警示，不会自动转化为安全性结论或候选淘汰结论；
- 实验优化与预测页面不构成实验设计、医疗或临床决策工具；
- 论文最终 10 个候选只用于筛选完成后的对照，不参与自动筛选。

## 数据来源、引用与许可

本仓库没有重新发布论文 PDF，也没有复制论文中可能含第三方权利的插图。筛选规则和演示数据参考：

> Liu, Xinyi; Uchigashima, Motokazu; Oomoto, Ikumi; Saito, Yoshihito; Uchida, Hitoshi; Oginezawa, Shinya; Masuda, Keiko; Satoh, Daisuke; Abe, Manabu; Sakimura, Kenji; Shimizu, Yoshihiro; Murayama, Masanori; Tainaka, Kazuki; and Mikuni, Takayasu. *SeeThrough: a rationally designed skull clearing technique for in vivo brain imaging*. Nature Communications 16, 7584 (2025). DOI: [10.1038/s41467-025-62836-1](https://doi.org/10.1038/s41467-025-62836-1).

Nature 将文章主体标为 CC BY 4.0；个别单独注明来源的第三方素材不在该许可范围内。`数据/论文原始数据/` 中的表格仅用于此研究演示，程序运行时会进行字段/类型清理、数值规则计算和结构映射等处理。完整的署名、许可与修改说明见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

项目代码未授予开源许可证；复用、修改或再分发不获授权。详见 [版权声明.md](版权声明.md)。
