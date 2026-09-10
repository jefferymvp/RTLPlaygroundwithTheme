#!/usr/bin/env python3
"""
RTLPlayground 本地 Web 仿真服务器 (兼容 Windows/Linux/macOS)
1:1 模拟 RTL837x 固件 httpd 与 API 行为
"""

import http.server
import socketserver
import json
import os
import sys
import time
import urllib.parse

PORT = 8088
HTML_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'html'))
SESSION_ID = "1234567890ab"
PASSWORD = "1234"

# 物理端口到逻辑端口映射 (SWGT024: 物理1~4为RJ45电口, 物理5~6为SFP+光口)
PHYS_TO_LOG = [4, 5, 6, 7, 8, 3]
PORTS_COUNT = 6
NSFP = 2

# 全局状态模拟
state = {
    "boot_time": time.time(),
    "last_called": time.time(),
    "tx_bytes": [1024 * 1024 * 50] * PORTS_COUNT,
    "rx_bytes": [1024 * 1024 * 180] * PORTS_COUNT,
    "tx_pkts": [52300] * PORTS_COUNT,
    "rx_pkts": [128400] * PORTS_COUNT,
    "port_names": ["Port 1 (PC)", "Port 2 (NAS)", "Port 3", "Port 4", "SFP+ 1 (10G)", "SFP+ 2 (10G)"],
    "port_speeds": ["auto"] * PORTS_COUNT,
    "cmd_history": ["System init completed", "Default IP 192.168.6.100 loaded"]
}

class RTLSimHandler(http.server.BaseHTTPRequestHandler):
    def is_authenticated(self):
        cookies = self.headers.get('Cookie', '')
        return f"session={SESSION_ID}" in cookies

    def send_json(self, data, status=200):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=UTF-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        query = urllib.parse.parse_qs(url.query)

        # 公开页面与静态资源（js/css/svg/png/ico）直接放行
        is_public = path == '/login.html' or path.endswith(('.js', '.css', '.svg', '.png', '.ico'))

        # 鉴权检查
        if not is_public and not self.is_authenticated():
            if path.endswith('.json') or path == '/cmd_log':
                self.send_response(401)
                self.end_headers()
                return
            else:
                self.send_response(302)
                self.send_header("Location", "/login.html")
                self.end_headers()
                return

        # 根路径跳转
        if path in ['/', '']:
            self.send_response(302)
            self.send_header("Location", "/index.html")
            self.end_headers()
            return

        # API 路由
        if path == '/status.json':
            now = time.time()
            dt = max(1.0, now - state["last_called"])
            state["last_called"] = now

            ports_data = []
            for i in range(1, PORTS_COUNT + 1):
                # 端口流量递增模拟
                rate = 250000000 if (i == 1) else (100000000 if (i == 2) else 0)
                state["tx_bytes"][i-1] += int(rate * dt * 0.4)
                state["rx_bytes"][i-1] += int(rate * dt * 0.6)
                state["tx_pkts"][i-1] += int(rate * dt / 1500 * 0.4)
                state["rx_pkts"][i-1] += int(rate * dt / 1500 * 0.6)

                is_sfp_port = 1 if (i > PORTS_COUNT - NSFP) else 0
                link_speed = 0
                if i == 1:
                    link_speed = 5  # 2.5G
                elif i == 2:
                    link_speed = 2  # 1G
                elif i == 5:
                    link_speed = 6  # 10G SFP+
                elif i == 6:
                    link_speed = 6  # 10G SFP+

                p = {
                    "portNum": i,
                    "logPort": PHYS_TO_LOG[i-1],
                    "isSFP": is_sfp_port,
                    "enabled": 1 if (i != 4) else 0,
                    "link": link_speed,
                    "txG": f"0x{state['tx_pkts'][i-1]:016x}",
                    "txB": f"0x0000000000000000",
                    "rxG": f"0x{state['rx_pkts'][i-1]:016x}",
                    "rxB": f"0x0000000000000000",
                    # 固件修复的真实字节字段
                    "txBytes": f"0x{state['tx_bytes'][i-1]:016x}",
                    "rxBytes": f"0x{state['rx_bytes'][i-1]:016x}"
                }

                if i <= len(state["port_names"]):
                    p["name"] = state["port_names"][i-1]

                if is_sfp_port:
                    p.update({
                        "sfp_vendor": "OEM-FIBER",
                        "sfp_model": f"10G-SFP+-0{i-4}",
                        "sfp_serial": f"SWGT2026090{i}",
                        "sfp_options": "0x68",
                        "sfp_temp": "0x28fb",
                        "sfp_vcc": "0x7eda",
                        "sfp_txbias": "0x0d24",
                        "sfp_txpower": "0x14bd",
                        "sfp_rxpower": "0x1120",
                        "sfp_laser": "0x0000"
                    })
                else:
                    p["adv"] = "100000" if i == 1 else "000011"

                ports_data.append(p)
            self.send_json(ports_data)
            return

        elif path == '/information.json':
            self.send_json({
                "ip_address": "192.168.6.100",
                "ip_gateway": "192.168.6.1",
                "ip_netmask": "255.255.255.0",
                "mac_address": "1c:2a:a3:23:00:02",
                "sw_ver": "v0.1.0-modern-ui",
                "hw_ver": "SWGT024-V2.0",
                "hostname": "RTL8372-Switch",
                "mgmt_vlan": 1
            })
            return

        elif path == '/eee.json':
            eee_data = []
            for i in range(1, PORTS_COUNT + 1):
                eee_data.append({
                    "portNum": i,
                    "isSFP": 1 if (i > PORTS_COUNT - NSFP) else 0,
                    "eee": "00000010",
                    "eee_lp": "00000100",
                    "active": 1 if (i % 2 == 1) else 0
                })
            self.send_json(eee_data)
            return

        elif path == '/bandwidth.json':
            bw_data = []
            for i in range(1, PORTS_COUNT + 1):
                bw_data.append({
                    "portNum": i,
                    "iLimited": 0,
                    "iFC": 0,
                    "iBW": "000fffff",
                    "eLimited": 0,
                    "eBW": "000fffff"
                })
            self.send_json(bw_data)
            return

        elif path == '/mirror.json':
            self.send_json({
                "mPort": 1,
                "enabled": 0,
                "mirror_tx": "0000000000000000",
                "mirror_rx": "0000000000000000"
            })
            return

        elif path == '/lag.json':
            lags = []
            for i in range(4):
                lags.append({
                    "lagNum": i,
                    "members": "0000000000000000",
                    "hash": "0x7e"
                })
            self.send_json(lags)
            return

        elif path == '/mtu.json':
            mtus = []
            for i in range(1, PORTS_COUNT + 1):
                mtus.append({
                    "portNum": i,
                    "mtu": "0x3fff" if (i % 2 == 1) else "0x05f2"
                })
            self.send_json(mtus)
            return

        elif path.startswith('/vlan.json'):
            self.send_json({
                "members": "0x00060011",
                "vlans": [
                    {"vid": 1, "members": 0x3f, "untagged": 0x3f, "mgmt": 1},
                    {"vid": 10, "members": 0x05, "untagged": 0x05, "mgmt": 0}
                ]
            })
            return

        elif path == '/vlanlist':
            self.send_json({
                "mgmt": 1,
                "vlan": [
                    {"id": 1, "name": "Default"},
                    {"id": 10, "name": "VLAN_10"}
                ]
            })
            return

        elif path == '/stp.json':
            self.send_json({
                "on": True,
                "rstp": True,
                "prio": 8,
                "hello": 2,
                "maxage": 20,
                "fwd": 15,
                "txhold": 6,
                "rootPrio": "8000",
                "rootMac": "1c2aa3230002",
                "myMac": "1c2aa3230002",
                "cost": "00000000",
                "weRoot": True,
                "rootPort": 0,
                "tc": "0001",
                "ports": [
                    {
                        "p": i,
                        "st": 3,
                        "role": 2,
                        "f": 1,
                        "pc": "00004e20",
                        "prio": 128,
                        "p2": 0,
                        "db": "80001c2aa3230002",
                        "dp": f"800{i}",
                        "dc": "00000000"
                    }
                    for i in range(1, PORTS_COUNT + 1)
                ]
            })
            return

        elif path.startswith('/counters.json'):
            # 52 个 MIB 计数器模拟数据
            counters = [f"0x{0x1000 + i * 37:016x}" for i in range(52)]
            self.send_json(counters)
            return

        elif path == '/cmd_log':
            body = "\n".join(state["cmd_history"]).encode('utf-8')
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=UTF-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # 静态文件服务
        file_path = os.path.normpath(os.path.join(HTML_DIR, path.lstrip('/')))
        if not file_path.startswith(HTML_DIR) or not os.path.isfile(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        mime_types = {
            ".html": "text/html; charset=UTF-8",
            ".css": "text/css; charset=UTF-8",
            ".js": "text/javascript; charset=UTF-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon"
        }
        _, ext = os.path.splitext(file_path)
        content_type = mime_types.get(ext.lower(), "application/octet-stream")

        with open(file_path, 'rb') as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8', errors='ignore')

        if self.path == '/login':
            params = urllib.parse.parse_qs(body)
            pwd = params.get('pwd', [''])[0]
            if pwd == PASSWORD:
                self.send_response(302)
                self.send_header("Location", "/index.html")
                self.send_header("Set-Cookie", f"session={SESSION_ID}; Path=/; SameSite=Strict")
                self.end_headers()
            else:
                self.send_response(302)
                self.send_header("Location", "/login.html?err=1")
                self.end_headers()
            return

        if not self.is_authenticated():
            self.send_response(401)
            self.end_headers()
            return

        if self.path == '/cmd':
            # 解析 cmd
            cmd_text = body.strip()
            if cmd_text.startswith("cmd="):
                cmd_text = urllib.parse.unquote(cmd_text[4:])
            state["cmd_history"].append(cmd_text)

            # 处理 port x name
            parts = cmd_text.split()
            if len(parts) >= 4 and parts[0] == "port" and parts[2] == "name":
                try:
                    p_num = int(parts[1])
                    p_name = " ".join(parts[3:])
                    if 1 <= p_num <= len(state["port_names"]):
                        state["port_names"][p_num - 1] = p_name
                except ValueError:
                    pass

            resp = b"OK"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
            return

        self.send_response(200)
        self.end_headers()

def run():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), RTLSimHandler) as httpd:
        print(f"[RTLPlayground Sim] Server running at http://127.0.0.1:{PORT}")
        sys.stdout.flush()
        httpd.serve_forever()

if __name__ == '__main__':
    run()
