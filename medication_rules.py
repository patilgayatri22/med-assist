def evaluate(order, tray):

    if tray.get("expired", False):
        return "hold","expired medication"

    if order["drug"]!=tray["drug"]:
        return "hold","drug mismatch"

    if order["dose"]!=tray["dose"]:
        return "hold","dose mismatch"

    return "proceed","checks passed"
