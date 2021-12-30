# -*- coding: utf-8 -*-
"""
flawfinder: C/C++安全扫描工具
功能: 代码分析
用法: python3 main.py
"""


import os
import json
import subprocess
import csv


class Flawfinder(object):
    def __get_task_params(self):
        """获取需要任务参数
        :return:
        """
        task_request_file = os.environ.get("TASK_REQUEST")
        with open(task_request_file, "r") as rf:
            task_request = json.load(rf)
        task_params = task_request["task_params"]

        return task_params

    def run(self):
        """
        :return:
        """
        # 代码目录直接从环境变量获取
        source_dir = os.environ.get("SOURCE_DIR", None)
        print("[debug] source_dir: %s" % source_dir)
        # 其他参数从task_request.json文件获取
        task_params = self.__get_task_params()
        # 规则
        rules = task_params["rules"]

        # ------------------------------------------------------------------ #
        # 增量扫描时,可以通过环境变量获取到diff文件列表,只扫描diff文件,减少耗时
        # 此处获取到的diff文件列表,已经根据项目配置的过滤路径过滤
        # ------------------------------------------------------------------ #
        # 需要扫描的文件后缀名
        want_suffix = (
            ".c",
            ".h",
            ".ec",
            ".ecp",  # Informix embedded C.
            ".pgc",  # Postgres embedded C.
            ".C",
            ".cpp",
            ".CPP",
            ".cxx",
            ".cc",  # C++
            ".CC",
            ".c++",  # C++.
            ".pcc",  # Oracle C++
            ".pc",  # Oracle SQL-embedded C
            ".sc",  # Oracle Pro*C pre-compiler
            ".hpp",
            ".H",  # .h - usually C++.
        )
        # 从 DIFF_FILES 环境变量中获取增量文件列表存放的文件(全量扫描时没有这个环境变量)
        diff_file_json = os.environ.get("DIFF_FILES")
        if diff_file_json:  # 如果存在 DIFF_FILES, 说明是增量扫描, 直接获取增量文件列表
            print("get diff file: %s" % diff_file_json)
            with open(diff_file_json, "r") as rf:
                diff_files = json.load(rf)
                scan_files = [
                    path for path in diff_files if path.lower().endswith(want_suffix)
                ]
        else:  # 未获取到环境变量,即全量扫描,遍历source_dir获取需要扫描的文件列表
            scan_files = [source_dir]

        error_output = "error_output.csv"
        result = []

        flawfinder_path = os.path.abspath("./tool/flawfinder.py")
        cmd = [
            "python3",
            flawfinder_path,
            "--columns",
            "--dataonly",
            "--quiet",
            "--singleline",
            "--csv",
            "--",
        ]

        if not scan_files:
            print("[error] 文件列表为空")
            return
        cmd.extend(scan_files)

        scan_cmd = " ".join(cmd)
        print("[debug] cmd: %s" % scan_cmd)
        fs_w = open(error_output, "w", encoding="utf-8")
        subprocess.run(cmd, stdout=fs_w, check=True, timeout=10)

        print("start data handle")
        # 数据处理
        try:
            with open(error_output, "r", encoding="utf-8", errors="replace") as fs_r:
                readers = csv.DictReader(fs_r)
                output_data = [row for row in readers]
        except:
            print("[error] 结果文件未找到或无法加载")
            return

        if output_data:
            for row in output_data:
                issue = {}
                issue["path"] = row["File"]
                issue["line"] = int(row["Line"])
                issue["column"] = int(row["Column"])
                issue["msg"] = row["Warning"]
                rule_name = row["Name"]
                if rule_name not in rules:
                    continue
                issue["rule"] = rule_name
                issue["refs"] = []
                if issue != {}:
                    result.append(issue)

        # 输出结果到指定的json文件
        with open("result.json", "w") as fp:
            json.dump(result, fp, indent=2)


if __name__ == "__main__":
    print("-- start run tool ...")
    Flawfinder().run()
    print("-- end ...")
