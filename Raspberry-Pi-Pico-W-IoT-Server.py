"""
Environment: Thonny IDE v4.1.6 and MicroPython v1.24.1.
Hardware: Raspberry Pi Pico W
Copyright: Released under CC BY-SA 4.0
Author: GitHub/OJStuff, December 08, 2024, v24.12
"""

from machine import Pin, ADC, PWM
import network
import socket
import utime
import ubinascii
import my_secrets

app_cfg = {
    # Configuration of application and network
    "board": "Raspberry Pi Pico W",
    "mode": "IoT Server",
    "ssid": my_secrets.my_ssid,  # Use a string for SSID if not using my_secrets module
    "pass": my_secrets.my_pass,  # Use a string for Password if not using my_secrets module
    "touch_control": False,
    "wifi_info": True,
    "ip": None,  # Will automatically be configured
    "mac": None,  # Will automatically be configured
    "gw": None,  # Will automatically be configured
    "port": 80,
}

port_cfg = [
    # Configuration of ports and functions
    # port_cfg[0] Active (1=Yes, 0=No)
    # port_cfg[1] Function (0 = Dig In, 1 = Dig Out, 2 = ADC In, 3 = PWM Out)
    # port_cfg[2] Value (and default value)
    #             For PWM, default value is PWM frequency, then PWM value is set to 0%
    # port_cfg[3] Name (GP port)
    # port_cfg[4] Comment (Description of port function)
    [1, 0, 0, "GP 0", "Digital In"],
    [1, 1, 1, "GP 1", "Digital Out"],
    [1, 1, 0, "GP 2", "Digital Out"],
    [1, 3, 50, "GP 3", "PWM LED (% dutycycle)"],
    [1, 0, 0, "GP 4", ""],
    [1, 0, 0, "GP 5", ""],
    [1, 0, 0, "GP 6", ""],
    [1, 0, 0, "GP 7", ""],
    [1, 0, 0, "GP 8", ""],
    [1, 0, 0, "GP 9", ""],
    [1, 0, 0, "GP 10", ""],
    [1, 0, 0, "GP 11", ""],
    [1, 0, 0, "GP 12", ""],
    [1, 0, 0, "GP 13", ""],
    [1, 0, 0, "GP 14", ""],
    [1, 1, 0, "GP 15", ""],
    [0, 0, 0, "GP 16", ""],
    [0, 0, 0, "GP 17", ""],
    [0, 0, 0, "GP 18", ""],
    [0, 0, 0, "GP 19", ""],
    [0, 0, 0, "GP 20", ""],
    [0, 0, 0, "GP 21", ""],
    [0, 0, 0, "GP 22", ""],
    [0, 0, 0, "GP 23", "Internal: Wireless Power On! Do not use!!!"],
    [0, 0, 0, "GP 24", "Internal: Wireless SPI Data. Do not use!!!"],
    [0, 0, 0, "GP 25", "Internal: Wireless SPI Chip-Select. Do not use!!!"],
    [1, 2, 0, "GP 26", "ADC ch=1, volts"],
    [1, 2, 0, "GP 27", "ADC ch=2, volts"],
    [1, 2, 0, "GP 28", "ADC ch=3, volts"],
    [1, 2, 0, "GP 29", "ADC ch=4, core temp (deg C)"],
]


def ports_init(ports: list) -> None:
    """
    Initiate 'ports' with default settings and values
    Args:
        ports: Table (list of lists) with values and default values
    Returns:
        None
    """
    pnr = -1
    for port in ports:
        pnr += 1
        if port[0] == 1:  # Port is active
            if port[1] == 0:  # Digital Input
                Pin(pnr, Pin.IN)
                port[2] = Pin(pnr).value()
            if port[1] == 1:  # Digital Output
                Pin(pnr, Pin.OUT)
                Pin(pnr).value(port[2])
            if port[1] == 2:  # ADC Input
                if pnr in [26, 27, 28]:
                    ADC(pnr)
                    port[2] = ADC(pnr).read_u16()
                if pnr == 29:
                    ADC(4)
                    port[2] = ADC(4).read_u16()
            if port[1] == 3:  # PWM Output
                PWM(Pin(pnr, Pin.OUT), freq=port[2])
                port[4] = port[4] + " " + str(port[2]) + " Hz"
                port[2] = 0
                PWM(Pin(pnr)).duty_u16(port[2])


def create_html(ports: list, config: dict) -> str:
    """
    Create HTML code for client, based on values in 'ports' and 'config'
    Args:
        ports: Table (list of lists) with values and default values
        config: Dictionary with configuration for the application
    Returns:
        A string with HTML code
    """

    def header() -> str:
        html_header = """
        <!DOCTYPE html>
        <html><head><style>
        table {font-family: courier; font-size: 20px; border-collapse: collapse; width: 100%;}
        button {width: 60px; height: 30px; font-size: 16px; font-weight: bold; text-align: center; border-radius: 8px;}
        td, th {border: 1px solid #dddddd; text-align: left; padding: 8px;}
        tr:nth-child(even) {background-color: #dddddd;}
        </style><meta http-equiv="refresh" content="60"></head>
        <br>
        """
        return html_header

    def user() -> str:
        html_user = "<a href=/><button>Home</button></a>"
        html_user += "<body><h2>" + config["board"] + " - " + config["mode"] + "</h2>"
        if config["touch_control"]:
            html_user += "<p><input checked type='checkbox' name='touch' value='off' id='radio1' "
            html_user += "onclick=\"{location.href='/touchcontrol-' + this.value;}\">Touchscreen</p>"
        else:
            html_user += (
                "<p><input type='checkbox' name='touch' value='on' id='radio1' "
            )
            html_user += "onclick=\"{location.href='/touchcontrol-' + this.value;}\">Touchscreen</p>"

        if config["wifi_info"]:
            html_user += "<p><input checked type='checkbox' name='touch' value='off' id='radio2' "
            html_user += "onclick=\"{location.href='/wifiinfo-' + this.value;}\">Network info</p>"
        else:
            html_user += (
                "<p><input type='checkbox' name='touch' value='on' id='radio2' "
            )
            html_user += "onclick=\"{location.href='/wifiinfo-' + this.value;}\">Network info</p>"
        return html_user

    def table() -> str:
        html_table = """
        <table>
        <tr><th>Port</th><th>Mode</th><th>Control</th><th>Value</th><th>Comment</th></tr>
        """
        pnr = -1
        for port in ports:
            port_oot = ["off", "on"]
            port_iot = ["Input", "Output", "Input", "Output"]
            port_ioc = ["red", "green"]
            pnr += 1
            html_line = ""
            if port[0] == 1:  # For every port in use, build html in table
                html_line += "        "
                html_line = (
                    "<tr><th>"
                    + str(port[3])
                    + "</th><th>"
                    + port_iot[port[1]]
                    + "</th>"
                )
                if port[1] == 1:  # Digital Output
                    html_line += (
                        "<th><a href=/P"
                        + str("{:02d}-on>".format(pnr))
                        + "<button>ON</button></a> <a href=/P"
                        + str("{:02d}-off>".format(pnr))
                        + "<button>OFF</button></a></th><th><font style=color:"
                        + port_ioc[port[2]]
                        + ";>"
                        + port_oot[port[2]]
                        + "</font></th><th>"
                        + port[4]
                        + "</th></tr>"
                    )
                if port[1] == 3:  # PWM Output
                    if config["touch_control"]:
                        html_line += (
                            "<th><input type='range' min='0' max='100' value='"
                            + str(port[2])
                            + "' step='5' class='slider' id='pot"
                            + str("{:02d}'".format(pnr))
                            + " ontouchend=\"{location.href='/P"
                            + str("{:02d}-'".format(pnr))
                            + " + this.value + 'pwm';}\""
                            + "></th><th><font style=color:black;>"
                            + str(port[2])
                            + "</font></th><th>"
                            + port[4]
                            + "</th></tr>"
                        )
                    else:
                        html_line += (
                            "<th><input type='range' min='0' max='100' value='"
                            + str(port[2])
                            + "' step='5' class='slider' id='pot"
                            + str("{:02d}'".format(pnr))
                            + " onmouseup=\"{location.href='/P"
                            + str("{:02d}-'".format(pnr))
                            + " + this.value + 'pwm';}\""
                            + "></th><th><font style=color:black;>"
                            + str(port[2])
                            + "</font></th><th>"
                            + port[4]
                            + "</th></tr>"
                        )
                if port[1] == 0:  # Digital Input
                    html_line += (
                        "<th></th><th><font style=color:"
                        + port_ioc[port[2]]
                        + ";>"
                        + port_oot[port[2]]
                        + "</font></th><th>"
                        + port[4]
                        + "</th></tr>"
                    )
                if port[1] == 2:  # ADC Input
                    html_line += (
                        "<th></th><th>"
                        + str(round(port[2], 2))
                        + "</th><th>"
                        + port[4]
                        + "</th></tr>"
                    )
                html_line += "\n        "
            html_table += html_line
        html_table += "</table>"
        return html_table

    def footer() -> str:
        if config["wifi_info"]:
            html_footer = f"""
            <p>Network info: SSID={config["ssid"]}, uC IP={config["ip"]}, uC MAC={config["mac"]}</p>
            </body></html>
            """
        else:
            html_footer = ""
        return html_footer

    return header() + user() + table() + footer()


def serve(connection, wlan, ports: list, config: dict) -> None:
    """
    Handle requests from client and respond with HTML code sent to client
    Args:
        connection: Network TCP connection, bound to IP address and port number
        wlan: WLAN interface object
        ports: Table (list of lists) with values and default values
        config: Dictionary with configuration for the application
    Returns:
        None
    """

    def req_eval(req):
        pval_status = False
        pnum_status = False
        pnum = 0
        pval = 0
        if "touchcontrol-on" in req:
            config["touch_control"] = True
        if "touchcontrol-off" in req:
            config["touch_control"] = False
        if "wifiinfo-on" in req:
            config["wifi_info"] = True
        if "wifiinfo-off" in req:
            config["wifi_info"] = False
        if req[2:4].isdigit():  # Handle portumber requests and table (port_cfg)
            pnum = int(req[2:4])
            pnum_status = True
            if "on" in req:
                pval = 1
                pval_status = True
                ports[pnum][2] = pval
                Pin(pnum).value(pval)
            if "off" in req:
                pval = 0
                pval_status = True
                ports[pnum][2] = pval
                Pin(pnum).value(pval)
            if "pwm" in req:
                req = req.strip("pwm")
                if req[5:].isdigit():
                    pval = int(req[5:])
                    pval_status = True
                    ports[pnum][2] = pval
                    PWM(Pin(pnum)).duty_u16(int(pval * 65535 / 100))
        pnum = -1
        for port in ports:  # Scan input ports and update values in table (port_cfg)
            pnum += 1
            if port[0] == 1:  # Port is active
                if port[1] == 0:  # Digital Input
                    port[2] = Pin(pnum).value()
                if port[1] == 2:  # ADC Input
                    if pnum in [26, 27, 28]:
                        port[2] = round(ADC(pnum).read_u16() * 3.3 / 65535, 2)
                    if pnum == 29:
                        port[2] = ADC(4).read_u16()
                        port[2] = round(
                            (27 - (ADC(4).read_u16() * 3.3 / 65535 - 0.706) / 0.001721),
                            2,
                        )
        return pnum_status == pval_status == True

    while wlan.isconnected():
        client = connection.accept()[0]
        request = str(client.recv(8192))
        try:
            request = request.split()[1]
        except IndexError:
            pass
        print(request)  # Print request from client in terminal
        status = req_eval(request)
        html = create_html(ports, config)
        client.send(html)
        client.close()


def main():
    ports_init(port_cfg)
    while True:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(app_cfg["ssid"], app_cfg["pass"])
        print(f"{app_cfg["board"]} - {app_cfg["mode"]}")
        while not wlan.isconnected():
            print(f"> Connecting to '{app_cfg["ssid"]}'")
            utime.sleep(0.5)
            utime.sleep(0.5)
        app_cfg["ip"] = wlan.ifconfig()[0]
        app_cfg["mac"] = ubinascii.hexlify(wlan.config("mac"), ":").decode()
        app_cfg["gw"] = wlan.ifconfig()[2]
        print(f"> Connecting to '{app_cfg["ssid"]}' succeeded!")
        print(
            f"> Network info: SSID={app_cfg["ssid"]}, uC IP={app_cfg["ip"]}, uC MAC={app_cfg["mac"]}"
        )
        address = (app_cfg["ip"], app_cfg["port"])
        connection = socket.socket()
        connection.bind(address)
        connection.listen(1)

        if wlan.isconnected():
            serve(connection, wlan, port_cfg, app_cfg)


if __name__ == "__main__":
    main()
