import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import requests
import json
import urllib3
import re
import threading

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CourseQueryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("抢课脚本 - 综合查询系统")
        self.root.geometry("1300x850") # 稍微调大一点以容纳新列

        # 数据缓存
        self.all_courses_cache = [] # 存储查询到的所有课程原始数据
        self.selected_jxb_ids = set() # 存储用户勾选的 JxbBh
        self.batch_list = []        # 存储选课清单 [{'JxbBh':..., 'Jxb':..., 'Xklb':..., 'Xkpc':...}]

        # 创建选项卡控件
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # === 选项卡 0：系统初始化 ===
        self.tab_init = tk.Frame(self.notebook)
        self.notebook.add(self.tab_init, text=" 系统初始化 ")
        self.setup_init_tab()

        # === 选项卡 1：课程查询 ===
        self.tab_courses = tk.Frame(self.notebook)
        self.notebook.add(self.tab_courses, text=" 课程查询 ")
        self.setup_course_query_tab()

        # === 选项卡 2：成绩查询 ===
        self.tab_scores = tk.Frame(self.notebook)
        self.notebook.add(self.tab_scores, text=" 成绩查询 ")
        self.setup_score_query_tab()

        # === 选项卡 3：批量选课 ===
        self.tab_batch = tk.Frame(self.notebook)
        self.notebook.add(self.tab_batch, text=" 批量选课 ")
        self.setup_batch_tab()

    # ==========================
    # Tab 0: 初始化
    # ==========================
    def setup_init_tab(self):
        frame = tk.LabelFrame(self.tab_init, text="初始化设置", padx=20, pady=20)
        frame.pack(padx=20, pady=20, fill="x")

        tk.Label(frame, text="TGT:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.init_tgt_entry = tk.Entry(frame, width=60)
        self.init_tgt_entry.grid(row=0, column=1, padx=5, pady=5)
        # self.init_tgt_entry.insert(0, "") # Default removed

        tk.Label(frame, text="Ticket (可选):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.init_ticket_entry = tk.Entry(frame, width=60)
        self.init_ticket_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame, text="Wengine:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.init_wengine_entry = tk.Entry(frame, width=60)
        self.init_wengine_entry.grid(row=2, column=1, padx=5, pady=5)
        # self.init_wengine_entry.insert(0, "") # Default removed

        btn_init = tk.Button(frame, text="开始初始化", command=self.run_initialization, bg="#FF9800", fg="white", font=("Arial", 12, "bold"), padx=20, pady=5)
        btn_init.grid(row=3, column=0, columnspan=2, pady=20)

        log_frame = tk.LabelFrame(self.tab_init, text="初始化日志", padx=10, pady=10)
        log_frame.pack(padx=20, fill="both", expand=True)
        self.log_text = tk.Text(log_frame, height=15)
        self.log_text.pack(fill="both", expand=True)

    def log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def run_initialization(self):
        threading.Thread(target=self._run_initialization_thread, daemon=True).start()

    def _run_initialization_thread(self):
        tgt = self.init_tgt_entry.get().strip()
        manual_ticket = self.init_ticket_entry.get().strip()
        wengine = self.init_wengine_entry.get().strip()

        if not tgt or not wengine:
            messagebox.showwarning("提示", "TGT 和 Wengine 不能为空")
            return

        self.log(">>> 开始初始化...")
        
        # Step 1
        st_url = f"https://webvpnnew.jxau.edu.cn/https/77726476706e69737468656265737421f3f652d22d286945300d8db9d6562d/lyuapServer/v1/tickets/{tgt}?vpn-12-o2-cas.jxau.edu.cn"
        headers_step1 = {
            "Host": "webvpnnew.jxau.edu.cn",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": f"wengine_vpn_ticketwebvpnnew_jxau_edu_cn={wengine};"
        }
        data_step1 = {"service": "https://jwgl.jxau.edu.cn/User/CheckTicketFromSSo", "loginToken": "loginToken"}

        fetched_ticket = None
        try:
            resp1 = requests.post(st_url, headers=headers_step1, data=data_step1, verify=False, timeout=10)
            if resp1.status_code == 200:
                fetched_ticket = resp1.text.strip()
                self.log(f"获取 Ticket 成功: {fetched_ticket}")
            else:
                self.log(f"获取 Ticket 失败: {resp1.status_code}")
        except Exception as e:
            self.log(f"请求异常: {str(e)}")

        final_ticket = manual_ticket if manual_ticket else fetched_ticket
        if not final_ticket:
            self.log("无可用 Ticket，初始化终止")
            return

        self.log(f"验证 Ticket: {final_ticket}")

        # Step 2
        check_url = f"https://webvpnnew.jxau.edu.cn/https/77726476706e69737468656265737421fae04690693a70516b468ca88d1b203b/User/CheckTicketFromSSo?ticket={final_ticket}"
        headers_step2 = headers_step1.copy()
        headers_step2["Sec-Fetch-Mode"] = "navigate"
        headers_step2.pop("Content-Type", None)

        try:
            resp2 = requests.get(check_url, headers=headers_step2, verify=False, allow_redirects=False, timeout=10)
            uuid_found = None
            if resp2.status_code == 302:
                location = resp2.headers.get("Location", "")
                self.log(f"302跳转: {location}")
                match = re.search(r'/Main/Index/([a-zA-Z0-9-]+)$', location)
                if match:
                    uuid_found = match.group(1)
            
            if uuid_found:
                self.log(f"成功获取 UUID: {uuid_found}")
                self.root.after(0, lambda: self._update_ui_entries(uuid_found, wengine))
            else:
                self.log("初始化失败: 未能提取 UUID")

        except Exception as e:
            self.log(f"验证异常: {str(e)}")

    def _update_ui_entries(self, uuid_val, wengine_val):
        for entry in [self.course_uuid_entry, self.score_uuid_entry]:
            entry.delete(0, "end")
            entry.insert(0, uuid_val)
        
        for entry in [self.course_wengine_entry, self.score_wengine_entry]:
            entry.delete(0, "end")
            entry.insert(0, wengine_val)
        
        messagebox.showinfo("初始化成功", "UUID 已自动填充")

    # ==========================
    # Tab 1: 课程查询
    # ==========================
    def setup_course_query_tab(self):
        # 顶部设置
        top_frame = tk.LabelFrame(self.tab_courses, text="查询设置", padx=5, pady=5)
        top_frame.pack(fill="x", padx=5, pady=5)

        tk.Label(top_frame, text="UUID:").grid(row=0, column=0, sticky="e")
        self.course_uuid_entry = tk.Entry(top_frame, width=35)
        self.course_uuid_entry.grid(row=0, column=1, padx=5)
        # self.course_uuid_entry.insert(0, "") # Default removed

        tk.Label(top_frame, text="Wengine:").grid(row=0, column=2, sticky="e")
        self.course_wengine_entry = tk.Entry(top_frame, width=25)
        self.course_wengine_entry.grid(row=0, column=3, padx=5)
        # self.course_wengine_entry.insert(0, "") # Default removed

        tk.Label(top_frame, text="查询数量(limit):").grid(row=0, column=4, sticky="e")
        self.course_limit_entry = tk.Entry(top_frame, width=8)
        self.course_limit_entry.grid(row=0, column=5, padx=5)
        self.course_limit_entry.insert(0, "200")

        btn_query = tk.Button(top_frame, text="获取所有课程", command=self.fetch_course_data, bg="#4CAF50", fg="white")
        btn_query.grid(row=0, column=6, padx=10)

        # 过滤栏
        filter_frame = tk.LabelFrame(self.tab_courses, text="多条件过滤", padx=5, pady=5)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        # 1. 课程名称
        tk.Label(filter_frame, text="名称/老师:").pack(side="left")
        self.course_filter_name = tk.Entry(filter_frame, width=15)
        self.course_filter_name.pack(side="left", padx=5)
        
        # 2. 上课时间
        tk.Label(filter_frame, text="时间:").pack(side="left")
        self.course_filter_time = tk.Entry(filter_frame, width=10)
        self.course_filter_time.pack(side="left", padx=5)

        # 3. 选课要求
        tk.Label(filter_frame, text="选课要求:").pack(side="left")
        self.course_filter_req = tk.Entry(filter_frame, width=10)
        self.course_filter_req.pack(side="left", padx=5)

        # 4. 是否已满
        self.course_filter_full_var = tk.IntVar()
        tk.Checkbutton(filter_frame, text="仅显示未满", variable=self.course_filter_full_var).pack(side="left", padx=10)
        
        # 绑定回车键
        for entry in [self.course_filter_name, self.course_filter_time, self.course_filter_req]:
            entry.bind("<Return>", lambda e: self.filter_courses())

        tk.Button(filter_frame, text="执行过滤", command=self.filter_courses, bg="#FFC107").pack(side="left", padx=10)
        
        self.lbl_course_count = tk.Label(filter_frame, text="总课程数: 0", fg="blue")
        self.lbl_course_count.pack(side="right", padx=20)

        # 选课按钮
        btn_add_batch = tk.Button(filter_frame, text="加入【批量选课】列表", command=self.add_selected_to_batch, bg="#2196F3", fg="white")
        btn_add_batch.pack(side="right", padx=10)

        # 表格
        tree_frame = tk.Frame(self.tab_courses)
        tree_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 增加 Xkyq (选课要求)
        cols = ("Check", "JxbBh", "Jxb", "Kclb", "RkLs", "SkRs", "MaxRs", "Sksj", "Xklb", "Xkyq")
        self.course_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")
        
        self.course_tree.heading("Check", text="选择")
        self.course_tree.heading("JxbBh", text="班级编号")
        self.course_tree.heading("Jxb", text="教学班名称")
        self.course_tree.heading("Kclb", text="课程类别")
        self.course_tree.heading("RkLs", text="老师")
        self.course_tree.heading("SkRs", text="已选")
        self.course_tree.heading("MaxRs", text="容量")
        self.course_tree.heading("Sksj", text="时间")
        self.course_tree.heading("Xklb", text="选课类别") # Need this for POST
        self.course_tree.heading("Xkyq", text="选课要求") # 新增

        # Config widths
        self.course_tree.column("Check", width=40, anchor="center")
        self.course_tree.column("JxbBh", width=100)
        self.course_tree.column("Jxb", width=200)
        self.course_tree.column("Kclb", width=80)
        self.course_tree.column("RkLs", width=80)
        self.course_tree.column("SkRs", width=50)
        self.course_tree.column("MaxRs", width=50)
        self.course_tree.column("Sksj", width=120)
        self.course_tree.column("Xklb", width=80)
        self.course_tree.column("Xkyq", width=150) # 新增

        self.course_tree.bind("<Button-1>", self.on_tree_click)
        self.course_tree.bind("<Double-1>", self.on_tree_double_click)

        scrolly = ttk.Scrollbar(tree_frame, orient="vertical", command=self.course_tree.yview)
        scrollx = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.course_tree.xview)
        self.course_tree.configure(yscroll=scrolly.set, xscroll=scrollx.set)
        scrolly.pack(side="right", fill="y")
        scrollx.pack(side="bottom", fill="x")
        self.course_tree.pack(side="left", fill="both", expand=True)

    def fetch_course_data(self):
        uuid = self.course_uuid_entry.get().strip()
        wengine = self.course_wengine_entry.get().strip()
        limit = self.course_limit_entry.get().strip()

        if not uuid or not wengine: 
            messagebox.showwarning("提示", "请先填写 UUID 和 Wengine")
            return

        url = f"https://webvpnnew.jxau.edu.cn/https/77726476706e69737468656265737421fae04690693a70516b468ca88d1b203b/KcManage/GxKcManage/GetKcInfo/{uuid}?vpn-12-o2-jwgl.jxau.edu.cn"
        headers = {
            "Host": "webvpnnew.jxau.edu.cn",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": f"wengine_vpn_ticketwebvpnnew_jxau_edu_cn={wengine};"
        }
        data = {"start": "0", "limit": limit}

        def _req():
            try:
                # Clear UI first
                self.root.after(0, self._clean_course_tree)
                
                res = requests.post(url, headers=headers, data=data, verify=False, timeout=15)
                jd = res.json()
                
                rows = jd.get("Data", [])
                if rows is None: rows = []
                
                # Cache data
                self.all_courses_cache = rows 
                
                self.root.after(0, lambda: self._populate_course_tree(rows))
                self.root.after(0, lambda: self.lbl_course_count.config(text=f"总课程数: {jd.get('totalCount', len(rows))}"))
                self.root.after(0, lambda: messagebox.showinfo("完成", f"已获取 {len(rows)} 门课程"))

            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))

        threading.Thread(target=_req, daemon=True).start()

    def _clean_course_tree(self):
        for i in self.course_tree.get_children():
            self.course_tree.delete(i)

    def _populate_course_tree(self, rows):
        self._clean_course_tree()
        for r in rows:
            # 安全获取 Xkyq
            xkyq = r.get("Xkyq", "")
            jxb_bh = r.get("JxbBh", "")
            
            check_mark = "☑" if jxb_bh in self.selected_jxb_ids else "☐"

            vals = (
                check_mark,
                jxb_bh,
                r.get("Jxb", ""),
                r.get("Kclb", ""),
                r.get("RkLs", ""),
                r.get("SkRs", ""),
                r.get("MaxRs", ""),
                r.get("Sksj", ""),
                r.get("Xklb", ""),
                xkyq
            )
            self.course_tree.insert("", "end", values=vals, tags=(json.dumps(r),))
    
    def on_tree_click(self, event):
        region = self.course_tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.course_tree.identify_column(event.x)
            if col == "#1": # 第一列 Check
                row_id = self.course_tree.identify_row(event.y)
                if row_id:
                    # 获取当前行数据
                    vals = list(self.course_tree.item(row_id, "values"))
                    # 这里的 vals 下标：0是Check, 1是JxbBh
                    jxb_bh = vals[1]
                    
                    if jxb_bh in self.selected_jxb_ids:
                        self.selected_jxb_ids.remove(jxb_bh)
                        vals[0] = "☐"
                    else:
                        self.selected_jxb_ids.add(jxb_bh)
                        vals[0] = "☑"
                    
                    self.course_tree.item(row_id, values=vals)
                    # 阻止后续默认选择事件传播（可选，但 tkinter 没有 preventDefault）
                    return "break"
    
    def on_tree_double_click(self, event):
        row_id = self.course_tree.identify_row(event.y)
        if row_id:
            vals = list(self.course_tree.item(row_id, "values"))
            jxb_bh = vals[1]
            
            if jxb_bh in self.selected_jxb_ids:
                self.selected_jxb_ids.remove(jxb_bh)
                vals[0] = "☐"
            else:
                self.selected_jxb_ids.add(jxb_bh)
                vals[0] = "☑"
            
            self.course_tree.item(row_id, values=vals)

    def filter_courses(self):
        if not self.all_courses_cache: return

        # 获取过滤条件
        name_kw = self.course_filter_name.get().strip().lower()
        time_kw = self.course_filter_time.get().strip().lower()
        req_kw = self.course_filter_req.get().strip().lower()
        only_not_full = self.course_filter_full_var.get() == 1

        filtered = []
        for r in self.all_courses_cache:
            # 1. 名称/老师过滤 (Jxb + RkLs)
            name_target = (str(r.get("Jxb", "")) + "|" + str(r.get("RkLs", ""))).lower()
            if name_kw and name_kw not in name_target:
                continue
            
            # 2. 时间过滤 (Sksj)
            time_target = str(r.get("Sksj", "")).lower()
            if time_kw and time_kw not in time_target:
                continue
                
            # 3. 选课要求过滤 (Xkyq)
            req_target = str(r.get("Xkyq", "")).lower()
            if req_kw and req_kw not in req_target:
                continue
            
            # 4. 是否已满过滤
            if only_not_full:
                try:
                    current = int(r.get("SkRs", 0))
                    capacity = int(r.get("MaxRs", 0))
                    if current >= capacity:
                        continue
                except:
                    pass

            filtered.append(r)
        
        self._populate_course_tree(filtered)
        self.lbl_course_count.config(text=f"当前显示: {len(filtered)} / {len(self.all_courses_cache)}")

    def add_selected_to_batch(self):
        if not self.selected_jxb_ids:
            messagebox.showinfo("提示", "请先在列表第一列勾选课程")
            return
        
        # 建立数据索引以便查找完整信息
        # 如果缓存很大，这里会有一点点耗时，但一般课程数也就几千，不碍事
        course_map = {str(r['JxbBh']): r for r in self.all_courses_cache}
        
        added_count = 0
        for jxb_bh in self.selected_jxb_ids:
            # 尝试从缓存获取数据
            raw_data = course_map.get(str(jxb_bh))
            if raw_data:
                # 去重检查
                exists = any(x['JxbBh'] == raw_data['JxbBh'] for x in self.batch_list)
                if not exists:
                    self.batch_list.append(raw_data)
                    added_count += 1
        
        self.refresh_batch_tree()
        messagebox.showinfo("添加成功", f"成功添加 {added_count} 门课程到批量列表\n（共勾选 {len(self.selected_jxb_ids)} 个）")

    # ==========================
    # Tab 2: 成绩查询 (Simple)
    # ==========================
    def setup_score_query_tab(self):
        frame = tk.LabelFrame(self.tab_scores, text="学生设置", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(frame, text="UUID:").grid(row=0, column=0, sticky="e")
        self.score_uuid_entry = tk.Entry(frame, width=35)
        self.score_uuid_entry.grid(row=0, column=1)
        # self.score_uuid_entry.insert(0, "") # Default removed

        tk.Label(frame, text="Wengine:").grid(row=0, column=2, sticky="e")
        self.score_wengine_entry = tk.Entry(frame, width=25)
        self.score_wengine_entry.grid(row=0, column=3)
        # self.score_wengine_entry.insert(0, "") # Default removed

        tk.Button(frame, text="查询成绩", command=self.fetch_score_data, bg="#2196F3", fg="white").grid(row=0, column=4, padx=10)

        tree_f = tk.Frame(self.tab_scores)
        tree_f.pack(fill="both", expand=True, padx=5, pady=5)
        self.score_tree = ttk.Treeview(tree_f, columns=("Xq", "Kcmc", "Zpcj", "Kscj", "Bz"), show="headings")
        self.score_tree.heading("Xq", text="学期")
        self.score_tree.heading("Kcmc", text="课程")
        self.score_tree.heading("Zpcj", text="总评")
        self.score_tree.heading("Kscj", text="考试")
        self.score_tree.heading("Bz", text="备注")
        self.score_tree.pack(fill="both", expand=True)

    def fetch_score_data(self):
        uuid = self.score_uuid_entry.get()
        wengine = self.score_wengine_entry.get()
        url = f"https://webvpnnew.jxau.edu.cn/https/77726476706e69737468656265737421fae04690693a70516b468ca88d1b203b/SystemManage/CJManage/GetXsCjByXh/{uuid}?vpn-12-o2-jwgl.jxau.edu.cn"
        headers = {"Host":"webvpnnew.jxau.edu.cn", "Cookie":f"wengine_vpn_ticketwebvpnnew_jxau_edu_cn={wengine};", "User-Agent":"Mozilla/5.0"}
        
        def _run():
            try:
                for i in self.score_tree.get_children(): self.score_tree.delete(i)
                res = requests.post(url, headers=headers, json={}, verify=False, timeout=15)
                data = res.json().get("Data", [])
                if data:
                    for r in data:
                        self.score_tree.insert("", "end", values=(r.get("Xq"), r.get("Kcmc"), r.get("Zpcj"), r.get("Kscj"), r.get("Bz")))
                    self.root.after(0, lambda: messagebox.showinfo("ok", f"获取 {len(data)} 条"))
                else:
                    self.root.after(0, lambda: messagebox.showinfo("info", "无数据"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("err", str(e)))
        threading.Thread(target=_run, daemon=True).start()

    # ==========================
    # Tab 3: 批量选课
    # ==========================
    def setup_batch_tab(self):
        btn_frame = tk.Frame(self.tab_batch, pady=10)
        btn_frame.pack(fill="x", padx=10)

        tk.Button(btn_frame, text="清空列表", command=self.clear_batch_list, bg="#f44336", fg="white").pack(side="left", padx=5)
        tk.Button(btn_frame, text="移除选中", command=self.remove_batch_item, bg="#FFC107").pack(side="left", padx=5)
        
        tk.Label(btn_frame, text=" | ").pack(side="left")
        
        tk.Button(btn_frame, text="一键极速抢课 (批量提交)", command=self.run_batch_xk, bg="#E91E63", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=20)

        # 列表
        self.batch_tree = ttk.Treeview(self.tab_batch, columns=("JxbBh", "Kcmc", "Status"), show="headings", height=15)
        self.batch_tree.heading("JxbBh", text="班级编号")
        self.batch_tree.heading("Kcmc", text="课程名称")
        self.batch_tree.heading("Status", text="抢课状态")
        
        self.batch_tree.column("JxbBh", width=120)
        self.batch_tree.column("Kcmc", width=300)
        self.batch_tree.column("Status", width=400)
        
        self.batch_tree.pack(fill="both", expand=True, padx=10, pady=5)

    def refresh_batch_tree(self):
        for i in self.batch_tree.get_children():
            self.batch_tree.delete(i)
        
        for item in self.batch_list:
            status = item.get("_status", "等待提交")
            self.batch_tree.insert("", "end", values=(item.get("JxbBh"), item.get("Jxb"), status))

    def clear_batch_list(self):
        self.batch_list = []
        self.refresh_batch_tree()

    def remove_batch_item(self):
        sel = self.batch_tree.selection()
        if not sel: return
        
        items_to_remove = []
        for i in sel:
            vals = self.batch_tree.item(i, "values")
            if vals:
                jxb_bh = str(vals[0])
                items_to_remove.append(jxb_bh)
        
        self.batch_list = [x for x in self.batch_list if str(x.get("JxbBh")) not in items_to_remove]
        self.refresh_batch_tree()

    def run_batch_xk(self):
        if not self.batch_list:
            messagebox.showinfo("提示", "列表为空")
            return
        
        uuid = self.course_uuid_entry.get().strip()
        wengine = self.course_wengine_entry.get().strip()
        
        if not uuid or not wengine:
            messagebox.showerror("错误", "请确认 ‘课程查询’ 页面的 UUID/Wengine 已填写，将使用该凭证抢课！")
            return

        threading.Thread(target=self._run_batch_thread, args=(uuid, wengine), daemon=True).start()

    def _run_batch_thread(self, uuid, wengine):
        url = f"https://webvpnnew.jxau.edu.cn/https/77726476706e69737468656265737421fae04690693a70516b468ca88d1b203b/KcManage/GxKcManage/XkInfo/{uuid}?vpn-12-o2-jwgl.jxau.edu.cn"
        headers = {
            "Host": "webvpnnew.jxau.edu.cn",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Cookie": f"wengine_vpn_ticketwebvpnnew_jxau_edu_cn={wengine};"
        }

        for i, item in enumerate(self.batch_list):
            item["_status"] = "正在提交..."
            self.root.after(0, self.refresh_batch_tree)

            payload = {
                "JxbBh": item.get("JxbBh"),
                "Xklb": item.get("Xklb"),
                "pcid": item.get("Xkpc")
            }
            
            try:
                res = requests.post(url, headers=headers, data=payload, verify=False, timeout=10)
                try:
                    jd = res.json()
                    success = jd.get("Result", False) or jd.get("success", False)
                    msg = jd.get("Message", "")
                    msg_clean = re.sub(r'<[^>]+>', '', msg)
                    
                    if success:
                        item["_status"] = f"成功: {msg_clean}"
                    else:
                        item["_status"] = f"失败: {msg_clean}"
                except:
                    item["_status"] = f"失败: 解析异常 {res.status_code}"

            except Exception as e:
                item["_status"] = f"请求错误: {str(e)}"
            
            self.root.after(0, self.refresh_batch_tree)

        self.root.after(0, lambda: messagebox.showinfo("结束", "批量抢课任务完成"))

if __name__ == "__main__":
    root = tk.Tk()
    app = CourseQueryApp(root)
    root.mainloop()
