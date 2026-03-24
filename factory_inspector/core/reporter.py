import sys
from typing import List
from factory_inspector.plugins.base import CheckResult

class ConsoleReporter:
    """输出到终端的结果展现器"""
    
    # ANSI 颜色定义
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    def report(self, results: List[CheckResult]):
        """在终端上打印彩色检测报告汇总"""
        print(f"\n{self.BOLD}--- 出厂检测报告 (Factory Inspection Report) ---{self.RESET}")
        
        all_pass = True
        for res in results:
            status_str = f"{self.GREEN}[PASS]{self.RESET}" if res.status else f"{self.RED}[FAIL]{self.RESET}"
            if not res.status:
                all_pass = False
            
            print(f"{status_str} {res.name}")
            print(f"       预期: {res.expected} | 实际: {res.actual}")
            if res.message:
                print(f"       原因: {res.message}")

        print(f"\n{self.BOLD}最终结论 (Grand Total):{self.RESET}", end=" ")
        if all_pass:
            print(f"{self.GREEN}全项检测通过 (ALL PASSED){self.RESET}")
        else:
            print(f"{self.RED}检测未通过 (INCOMPLETE/FAILED){self.RESET}")
        print("-" * 50)
        
        # 退出码
        # sys.exit(0 if all_pass else 1)
