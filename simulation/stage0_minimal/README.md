# stage0_minimal

这是按你希望的 **stage 风格**整理的第一阶段最小仿真包。

## 目录结构

```text
stage0_minimal/
├── src/
│   └── rfa_stage0/
│       ├── cli/
│       │   ├── preview_geometry.py
│       │   ├── calibrate_source_scale.py
│       │   └── run_case.py
│       ├── geometry.py
│       ├── io_utils.py
│       ├── metrics.py
│       ├── plotting.py
│       └── solver_fd.py
├── configs/
│   └── base.yaml
├── outputs/              # 运行后自动写入 figures / metrics / cases
├── requirements.txt
├── run_all.sh
└── README.md
```

## 放到你的总目录里

建议放到：

```text
liver_rfa/
└── simulation/
    └── stage0_minimal/
```

如果你更想统一成 `cardiac_rfa/` 这种命名风格，也可以直接改最外层项目名，内部代码不受影响。

## 当前 stage0 的目标

这一版只做三件事：

1. 画几何图
2. 做无血管基线校准建议
3. 跑一个单病例，输出 figure + metrics + npz

## 环境准备（macOS）

在 `stage0_minimal/` 目录下执行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
export PYTHONPATH=$PWD/src
```

## 运行方式

### 一键运行
```bash
bash run_all.sh
```

### 分步运行
```bash
export PYTHONPATH=$PWD/src

python -m rfa_stage0.cli.preview_geometry --config configs/base.yaml
python -m rfa_stage0.cli.calibrate_source_scale --config configs/base.yaml --target-equivalent-diameter-mm 22 --search-min 1 --search-max 1e4 --num 20
python -m rfa_stage0.cli.run_case --config configs/base.yaml
```

## 输出文件

运行后会自动生成：

- `outputs/figures/<case_id>_geometry.png`
- `outputs/figures/<case_id>_overview.png`
- `outputs/metrics/<case_id>.json`
- `outputs/cases/<case_id>.npz`

## 配置文件

当前唯一需要改的是：

- `configs/base.yaml`

默认是 **stage0 无血管基线**：
- `disable_vessel: true`
- `case_id: stage0_novessel_p50_t8`

## 当前模型范围

- 2D
- 单肿瘤
- 单电极
- 单血管（但 stage0 默认关闭血管）
- 电势 + 焦耳热 + Pennes + Arrhenius

## 建议的后续阶段

```text
simulation/
├── stage0_minimal/
├── stage1_novessel_baseline/
├── stage2_single_vessel/
├── stage3_gap_sweep/
└── stage4_publishable/
```
