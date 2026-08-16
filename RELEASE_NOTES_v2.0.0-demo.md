# Amadeus v2.0.0-demo

Amadeus Demo 2.0 将 SeeThrough 候选筛选工作流整理为可直接运行的 Streamlit 演示：可查看筛选过程、候选与化学信息，生成 Excel 报告，并以交互式图表和 PNG/SVG 图展示结果。

## 本版重点

- 统一产品名：**Amadeus: Automated Screening Framework**；
- 新增交互式筛选流程柱状图与候选参数散点图；
- 保留可下载的 Excel、PNG 和 SVG 结果；
- 结果展示与核心计算解耦，可通过 `AMADEUS_ENABLE_RESULT_VISUALIZATION=0` 临时关闭图表；
- 明确预测与实验优化仍是接口预留，避免将研究原型误作验证完成的软件。

完整变更见 [CHANGELOG.md](CHANGELOG.md)。这是研究原型，不用于直接证明安全性、透明化效果或临床适用性。
