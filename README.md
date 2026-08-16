# Amadeus: Automated Screening Framework

**Demo 2.0**｜颅骨透明化试剂候选筛选研究原型

Amadeus 将 SeeThrough 论文补充数据中的候选物，经可配置数值规则、RDKit 结构处理和 Hansen 溶解度参数距离计算，形成可追溯的候选筛选结果、交互式结果视图和可下载报告。

> 研究原型，不用于直接证明安全性、透明化效果或临床适用性。

## 现在能做什么

- 导入、清理和标准化 SeeThrough 补充数据及用户候选表；
- 执行可配置数值规则筛选，记录每步候选数量与逐候选审计信息；
- 进行化合物身份核验、RDKit 结构/描述符处理和 Hansen 距离计算；
- 在 Streamlit 界面中查看候选、化学信息、规则、毒性证据和配方构建工作流；
- 在“规则筛选”页面查看筛选流程柱状图、候选参数交互式散点图，以及可下载 PNG/SVG 图；
- 导出 Excel 筛选报告和派生结果图表。

当前 SeeThrough 水相候选演示计算链为 **1619 → 1373 → 1297 → 225 → 41 → 20**；自动规则获得 20 个候选，论文最终 10 个候选在自动候选中恢复 **10/10**。

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

## 结果可视化

Demo 默认启用结果可视化。核心计算与展示层相互独立：关闭图表不会影响筛选、报告导出或结果保存。

### 公开演示结果

以下两张图由仓库内的 SeeThrough 补充数据运行 Demo 2.0 生成：筛选数量链为 **1619 → 1373 → 1297 → 225 → 41 → 20**，论文最终 10 个候选在自动候选中恢复 **10/10**。它们是可复现的演示输出，不构成安全性、透明化效果或临床结论。

![SeeThrough 候选试剂自动筛选数量变化](数据/导出结果/图表/候选试剂筛选数量变化图.png)

![自动筛选候选的物化参数分布](数据/导出结果/图表/最终候选物化参数分布图.png)

相同图表也提供为 SVG 文件，便于在报告或幻灯片中无损使用。

开发新规则或调整输出字段时，可以临时关闭：

```powershell
$env:AMADEUS_ENABLE_RESULT_VISUALIZATION = "0"
streamlit run 启动程序.py
```

重新打开 PowerShell 或设置为 `1` 后，图表会恢复。该开关适合在核心逻辑尚未稳定时避免界面兼容性干扰开发。

## 模块状态

| 模块 | 状态 | 当前输出 |
| --- | --- | --- |
| 论文/用户候选导入、字段映射与身份处理 | 已实现 | 标准化候选记录、身份映射与冲突记录 |
| RDKit 描述符与 Hansen 距离 | 已实现 | 结构映射、描述符、与 BA/VA 的距离 |
| SeeThrough 规则筛选与报告/图表导出 | 已实现 | 筛选记录、自动候选、Excel、PNG/SVG |
| 毒性证据视图 | 部分实现 | 本地/可选公开来源证据与警示 |
| 透明化预测 | 接口预留 | 无校准训练数据时不输出虚构预测 |
| 实验优化 | 接口预留 | 等待实验历史与明确优化目标 |

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
