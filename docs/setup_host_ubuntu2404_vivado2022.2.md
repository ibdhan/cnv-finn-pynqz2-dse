# Host setup: Ubuntu 24.04 + Vivado/Vitis HLS 2022.2

Verified on a ThinkPad laptop (16 threads, 14 GiB RAM + 4 GiB swap, Ubuntu 24.04, Docker 29). FINN v0.10.1 is paired with
Vivado 2022.2; the FINN container itself is Ubuntu 22.04, so Ubuntu 24.04 on the host only matters for the Vivado installer.

## Requirements
- ≥100 GB free disk (Vivado 2022.2 with Zynq-7000 only + FINN image + build folders of a sweep).
- AMD account to download `Xilinx_Unified_2022.2_1014_8888_Lin64.bin`.

## 1. Legacy libraries for the installer on Ubuntu 24.04
Without them the installer can hang at "Generating installed device list".
```bash
cd ~/Downloads && rm -f libtinfo5_*.deb libncurses5_*.deb
B=http://security.ubuntu.com/ubuntu/pool/universe/n/ncurses
A=http://archive.ubuntu.com/ubuntu/pool/universe/n/ncurses
wget -q $B/libtinfo5_6.3-2ubuntu0.2_amd64.deb && wget -q $B/libncurses5_6.3-2ubuntu0.2_amd64.deb \
  || { rm -f libtinfo5_*.deb libncurses5_*.deb; wget -q $A/libtinfo5_6.3-2_amd64.deb && wget -q $A/libncurses5_6.3-2_amd64.deb; }
sudo apt install ./libtinfo5_*.deb ./libncurses5_*.deb
sudo apt install -y build-essential libx11-6 libxrender1 libxtst6 libxi6 locales
dpkg -l | grep -E "libtinfo5|libncurses5"    # two "ii" lines with identical versions
```
Security revisions of these packages change over time (old URLs may return 404); the fallback above uses the archive.

## 2. Install Vivado 2022.2
```bash
chmod +x ~/Downloads/Xilinx_Unified_2022.2_1014_8888_Lin64.bin
~/Downloads/Xilinx_Unified_2022.2_1014_8888_Lin64.bin      # no sudo
```
Wizard: Vivado → ML Standard → Vivado + **Vitis HLS** → devices **Zynq-7000 only** → install path `/tools/Xilinx`.
The "unsupported OS" warning can be ignored.

## Verify
```bash
source /tools/Xilinx/Vivado/2022.2/settings64.sh && vivado -version | head -2 && vitis_hls -version | head -2
```
Versions used in the paper: Vivado/Vitis HLS 2022.2 (SW Build 3671981 / 3670227).

## Common problems
| Symptom | Cause | Fix |
|---|---|---|
| installer stuck at "Generating installed device list" | libtinfo5/libncurses5 missing | step 1, rerun installer |
| `wget` of libtinfo5 returns 404 | package revision replaced | use the fallback in step 1 |
| `vivado: command not found` | 2025.x and 2022.2 use different folder layouts | check `ls /tools/Xilinx` |
