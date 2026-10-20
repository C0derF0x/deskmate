import platform
import psutil


def get_system_info():
    # CPU
    cpu_usage = psutil.cpu_percent(interval=0.5)

    # RAM
    memory = psutil.virtual_memory()
    ram_usage = memory.percent
    ram_total = round(memory.total / (1024 ** 3), 1)
    ram_used = round(memory.used / (1024 ** 3), 1)

    # Disk
    disk = psutil.disk_usage("/")
    disk_usage = disk.percent
    disk_total = round(disk.total / (1024 ** 3), 1)
    disk_used = round(disk.used / (1024 ** 3), 1)

    # Operating system
    operating_system = platform.system()
    os_version = platform.release()

    return {
        "os": f"{operating_system} {os_version}",
        "cpu_usage": cpu_usage,
        "ram_usage": ram_usage,
        "ram_used": ram_used,
        "ram_total": ram_total,
        "disk_usage": disk_usage,
        "disk_used": disk_used,
        "disk_total": disk_total,
    }

def format_system_info():
    info = get_system_info()

    return (
        f"OS: {info['os']}\n"
        f"CPU usage: {info['cpu_usage']}%\n"
        f"RAM: {info['ram_used']} GB / {info['ram_total']} GB "
        f"({info['ram_usage']}%)\n"
        f"Disk: {info['disk_used']} GB / {info['disk_total']} GB "
        f"({info['disk_usage']}%)"
    )