window.MNS_MOCK_REPORTS = [
  {
    task_id: "analysis-demo-600519",
    stock: { code: "600519", name: "贵州茅台", market: "cn" },
    status: "report_ready",
    action: "watch",
    confidence: "medium",
    summary: "趋势仍偏稳，等待更清晰的量价确认。",
    reasons: ["价格位于主要均线附近", "估值数据已进入上下文", "当前报告来自 Web 离线演示数据"],
    risks: [{ level: "medium", message: "短期波动可能放大，需结合真实数据复核" }],
    agent_views: [
      { agent: "Market Analyst", conclusion: "价格结构保持韧性，但量能确认不足" },
      { agent: "Risk Analyst", conclusion: "建议控制仓位并等待确认信号" }
    ],
    data_gaps: ["fund_flow"],
    data_diagnostics: [
      { kind: "quote", source: "tencent", ok: true, error_type: null, error_message: null, fetched_at: null, is_stale: false }
    ],
    risk_controls: {
      max_position_pct: 0.05,
      stop_loss_pct: 0.08,
      take_profit_pct: 0.15,
      time_horizon: "5-20 个交易日",
      rules: [
        { name: "confidence", level: "medium", message: "中等置信度设定仓位上限" },
        { name: "data_gaps", level: "medium", message: "存在资金流数据缺口，仓位上限降至 5%" }
      ],
      disclaimer: "本报告仅用于研究和复盘，不构成投资建议；任何交易决策需由用户自行承担风险。"
    },
    data_context: {
      stock: { code: "600519", name: "贵州茅台", market: "cn" },
      quote: { price: 1688, source: "tencent" },
      technicals: { ma5: 1660, ma10: 1625, ma20: 1588 },
      fundamentals: { pe_ttm: 28.5, pb: 9.1 },
      news: [{ title: "示例新闻：业绩保持稳定" }],
      gaps: ["fund_flow"],
      diagnostics: []
    }
  },
  {
    task_id: "analysis-demo-000001",
    stock: { code: "000001", name: "平安银行", market: "cn" },
    status: "report_ready",
    action: "watch",
    confidence: "low",
    summary: "银行板块处于修复观察区，需等待基本面和资金面共同确认。",
    reasons: ["估值处于低位区间", "技术面仍缺少趋势突破", "新闻上下文较少"],
    risks: [{ level: "low", message: "报告使用离线演示数据，不构成投资建议" }],
    agent_views: [
      { agent: "Fundamentals Analyst", conclusion: "估值具备观察价值，但盈利弹性仍需验证" },
      { agent: "News Analyst", conclusion: "缺少新的高置信事件驱动" }
    ],
    data_gaps: ["news"],
    data_diagnostics: [
      { kind: "news", source: "static", ok: false, error_type: "MissingData", error_message: "离线演示新闻不足", fetched_at: null, is_stale: false }
    ],
    risk_controls: {
      max_position_pct: 0.05,
      stop_loss_pct: 0.08,
      take_profit_pct: 0.15,
      time_horizon: "5-20 个交易日",
      rules: [
        { name: "confidence", level: "low", message: "低置信度限制仓位" },
        { name: "data_gaps", level: "medium", message: "存在新闻数据缺口，仓位上限降至 5%" }
      ],
      disclaimer: "本报告仅用于研究和复盘，不构成投资建议；任何交易决策需由用户自行承担风险。"
    },
    data_context: {
      stock: { code: "000001", name: "平安银行", market: "cn" },
      quote: { price: 10.8, source: "static" },
      technicals: { ma5: 10.6, ma10: 10.4, ma20: 10.2 },
      fundamentals: { pe_ttm: 5.8, pb: 0.62 },
      news: [],
      gaps: ["news"],
      diagnostics: []
    }
  }
];
