# PYNQ-Z2 board setup (image, direct Ethernet link, FINN driver dependencies)

Verified with PYNQ image **v3.1** (`pynq` 3.1.1, kernel 6.6, Python 3.10.4). FINN v0.10.1 drivers and Vivado 2022.2
bitstreams run on this image; flashing v3.0.1 is not required.

## A. Direct link host ↔ board (host side, once)
The board is connected with a single Ethernet cable and has no gateway/internet. Example with NetworkManager
(replace `enp5s0` with your wired interface):
```bash
nmcli con add type ethernet ifname enp5s0 con-name pynq-direct \
  ipv4.method manual ipv4.addresses 192.168.2.1/24 ipv6.method disabled connection.autoconnect no
nmcli con up pynq-direct && ping -c 3 192.168.2.99
ssh-copy-id xilinx@192.168.2.99          # default password: xilinx
```
No gateway is set, so the host keeps its normal internet route.

## B. Every session
- The board has no RTC/internet; set its clock from the host before measuring (timestamps otherwise go back in time):
  `ssh -t xilinx@192.168.2.99 "sudo date -u -s '$(date -u '+%F %T')'"` (done automatically by `measure_on_board.sh`).
- Shut down with `sudo shutdown -h now`.

## C. Running a FINN accelerator on PYNQ 3.x: root + pynq_venv + **xrt_setup**
PYNQ 3.x finds the FPGA through XRT; without `xrt_setup.sh` you get `RuntimeError: No Devices Found`.
Use the wrapper `code/deploy/pynq_run.sh`:
```bash
sudo ./pynq_run.sh python3 validate_npz.py --npz ~/cifar10_test.npz --batchsize 1000
sudo ./pynq_run.sh python3 driver.py --exec_mode=throughput_test --batchsize 1000
```

## D. Optional: passwordless sudo for user `xilinx`
Used so that `measure_on_board.sh` does not prompt repeatedly. Acceptable only because the board is on an isolated
point-to-point link. **Remove it before connecting the board to a shared network.**
```bash
ssh -t xilinx@192.168.2.99 "echo 'xilinx ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/010-xilinx-nopasswd >/dev/null && sudo chmod 440 /etc/sudoers.d/010-xilinx-nopasswd && sudo visudo -c"
# undo: sudo rm /etc/sudoers.d/010-xilinx-nopasswd
```

## E. Offline Python package for the FINN driver: bitstring
On the host: `python3 -m pip download bitstring==3.1.9 --no-deps -d . && scp bitstring-3.1.9* xilinx@192.168.2.99:~/`
On the board: `source /etc/profile.d/pynq_venv.sh && sudo $(which pip3) install --no-index ~/bitstring-3.1.9*`
(use the venv's pip; bitstring 3.1.9 is pure Python, 4.x needs a compiled `bitarray`).

## F. Test set
The board cannot download CIFAR-10. Create `cifar10_test.npz` on the host with
`code/analysis/make_cifar10_npz.py` (inside the FINN container); `measure_on_board.sh` copies it to the board.

## Common problems
| Symptom | Cause | Fix |
|---|---|---|
| wired interface stuck at "getting IP configuration" | default DHCP profile, the board has no DHCP server | activate `pynq-direct` |
| `RuntimeError: No Devices Found` | only `pynq_venv.sh` sourced under `sudo bash -c` | also source `xrt_setup.sh` (use `pynq_run.sh`) |
| result files dated in the past | board clock not synchronised | set the clock from the host (B) |
| `/etc/os-release` says "3.0 (Carlisle)" | label not updated in the v3.1 image | trust `pip3 show pynq` |
