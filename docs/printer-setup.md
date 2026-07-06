# Printer Setup

## Target

- Model: Zebra / ZDesigner ZD421
- DPI: 203
- Language: ZPL
- Label: 4x6 inches
- Canvas: 812x1218 dots

## Baseline Test

Generate a test file without printing:

```powershell
python .\src\zebra_label_gateway\print_tcp.py --host 192.168.x.x --save-only
```

Check network reachability:

```powershell
Test-NetConnection <actual-printer-ip> -Port 9100
```

Print the test label:

```powershell
python .\src\zebra_label_gateway\print_tcp.py --host <actual-printer-ip>
```

## Notes To Record

- Connection method:
- Printer IP:
- Windows queue name:
- Media type:
- Darkness:
- Speed:
- Calibration result:
- Orientation result:
