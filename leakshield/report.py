"""格式化报告生成"""
from leakshield.result import LeakageResult


def format_report(result: LeakageResult) -> str:
    """
    生成格式化的检测报告

    Args:
        result: 检测结果

    Returns:
        格式化的报告文本
    """
    lines = []

    # 标题
    lines.append("╔══════════════════════════════════════════╗")
    lines.append("║         LeakShield 检测报告              ║")
    lines.append("╚══════════════════════════════════════════╝")
    lines.append("")

    # 数据集信息
    if result.train_shape and result.test_shape:
        lines.append(
            f"训练集: {result.train_shape}   测试集: {result.test_shape}"
        )
    lines.append("")

    # 综合风险等级
    level_display = result.overall_level.upper()
    score_display = f"{result.overall_score:.2f}"

    # 根据风险等级添加颜色标记（使用 rich 标记）
    if result.overall_level == "high":
        level_color = "[bold red]"
    elif result.overall_level == "medium":
        level_color = "[bold yellow]"
    elif result.overall_level == "low":
        level_color = "[bold blue]"
    else:
        level_color = "[bold green]"

    lines.append(
        f"综合风险等级: {level_color}{level_display}[/]  (score: {score_display})"
    )
    lines.append("")

    # 检测项详情
    if result.items:
        for idx, item in enumerate(result.items, 1):
            lines.append(f"[{idx}] {item.leakage_type}  ▶  {item.risk_level.upper()}")
            lines.append(f"    依据: {item.taxonomy_ref}")
            lines.append(
                f"    影响: {item.affected_count} / {result.test_shape[0] if result.test_shape else '?'} "
                f"({item.affected_ratio * 100:.1f}%)"
            )
            lines.append(f"    说明: {item.detail}")
            lines.append(f"    修复: {item.fix_hint}")
            lines.append("─────────────────────────────────────────")

        lines.append(f"共发现 {len(result.items)} 项泄露风险")
    else:
        lines.append("[bold green]✓ 未检测到数据泄露风险[/]")

    lines.append("")

    # 引擎版本信息
    if result.engine_versions:
        lines.append("检测引擎版本:")
        for engine_name, version in result.engine_versions.items():
            lines.append(f"  - {engine_name}: {version}")

    return "\n".join(lines)
