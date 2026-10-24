def before_command(cmd: str):
    blocked = ["rm -rf /", "curl http://evil", "wget http://evil"]
    for b in blocked:
        if b in cmd:
            raise Exception("CommandBlockedError")
    return True
