"""命令行接口"""
import sys
from pathlib import Path

import click
import pandas as pd
from rich.console import Console

from leakshield import __version__, check
from leakshield.config import DetectionConfig

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="leakshield")
def main():
    """LeakShield - 轻量级机器学习数据泄露检测工具"""
    pass


@main.command()
@click.argument("train_csv", type=click.Path(exists=True))
@click.argument("test_csv", type=click.Path(exists=True))
@click.option(
    "--output",
    type=click.Choice(["text", "json"], case_sensitive=False),
    default="text",
    help="输出格式：text 或 json",
)
@click.option(
    "--task-type",
    type=click.Choice(["auto", "classification", "regression", "timeseries"], case_sensitive=False),
    default="auto",
    help="任务类型",
)
@click.option(
    "--output-file",
    type=click.Path(),
    default=None,
    help="JSON 输出文件路径（仅当 --output=json 时有效）",
)
def check_cmd(train_csv: str, test_csv: str, output: str, task_type: str, output_file: str):
    """
    检测训练集和测试集之间的数据泄露

    示例:

        leakshield check train.csv test.csv

        leakshield check train.csv test.csv --output json --output-file result.json
    """
    try:
        # 读取 CSV 文件
        console.print(f"[cyan]正在读取训练集: {train_csv}[/cyan]")
        train_df = pd.read_csv(train_csv)

        console.print(f"[cyan]正在读取测试集: {test_csv}[/cyan]")
        test_df = pd.read_csv(test_csv)

        # 创建配置
        config = DetectionConfig(task_type=task_type)

        # 执行检测
        console.print("[cyan]正在执行泄露检测...[/cyan]")
        result = check(train_df, test_df, config)

        # 输出结果
        if output.lower() == "json":
            if output_file:
                result.to_json(output_file)
                console.print(f"[green]✓ 结果已保存到: {output_file}[/green]")
            else:
                import json
                console.print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            result.report()

        # 根据风险等级设置退出码
        if result.overall_level == "high":
            sys.exit(2)
        elif result.overall_level == "medium":
            sys.exit(1)
        else:
            sys.exit(0)

    except Exception as e:
        console.print(f"[red]错误: {str(e)}[/red]")
        sys.exit(3)


if __name__ == "__main__":
    main()
