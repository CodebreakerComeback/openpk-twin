# OpenPK-Twin

### Open-source pharmacokinetic modelling and virtual patient simulation toolkit

**Explore drug behaviour. Simulate virtual populations. Reproduce pharmacokinetic experiments.**

OpenPK-Twin is an open-source Python-based toolkit for pharmacokinetic (PK) modelling, plasma concentration–time simulation, and virtual patient population analysis.

The project provides computational implementations of one-compartment and two-compartment intravenous bolus models, together with Monte Carlo-based population simulation, inter-individual variability analysis, data visualization, and reproducible CSV exports.

OpenPK-Twin aims to make foundational pharmacokinetic modelling more accessible to pharmacy students, pharmaceutical scientists, pharmacometricians, researchers, and developers through transparent, reusable, and well-documented computational tools.

**Live platform:** https://openpk-twin.vercel.app

**Backend API:** https://openpk-twin-api.onrender.com

**Interactive API documentation:** https://openpk-twin-api.onrender.com/docs

---

## 1. Project Overview

Pharmacokinetic modelling is fundamental to understanding drug absorption, distribution, metabolism, and elimination. Mathematical models help describe how drug concentrations change over time and how inter-individual variability influences drug disposition.

However, learning and experimenting with pharmacokinetic models can require specialized software, programming knowledge, and computational resources.

OpenPK-Twin addresses this accessibility gap through an open-source computational environment that combines pharmacokinetic modelling, virtual population simulation, and interactive visualization.

The platform currently supports two foundational pharmacokinetic models and allows users to explore population-level concentration–time behaviour through configurable simulation parameters.

## 2. Core Features

### Pharmacokinetic modelling

- One-compartment intravenous bolus model.
- Two-compartment intravenous bolus model.
- Plasma concentration–time profile generation.
- Configurable pharmacokinetic parameters.
- Simulation over user-defined sampling times.

### Virtual patient simulation

- Monte Carlo-based population simulation.
- Simulation of up to 10,000 virtual patients through the web interface.
- Configurable inter-individual variability.
- Random seed-based reproducibility.
- Population median concentration profiles.
- 5th–95th percentile population intervals.
- Representative virtual patient concentration profiles.

### Data visualization and export

- Interactive concentration–time visualization.
- Population median and percentile visualization.
- Representative patient profiles.
- CSV export of simulation results.
- Reproducibility metadata accompanying exported datasets.

### Backend and deployment

- Python-based computational engine.
- FastAPI backend.
- React and Vite frontend.
- REST API endpoints for population simulation.
- Automated GitHub Actions testing.
- Production deployment using Render and Vercel.

## 3. Pharmacokinetic Models

### 3.1 One-compartment intravenous bolus model

The one-compartment model represents the body as a single, well-mixed compartment.

Following an intravenous bolus administration, the plasma concentration decreases according to first-order elimination.

The concentration–time relationship is:

\[
C(t)=\frac{D}{V_d}e^{-kt}
\]

Where:

- \(C(t)\) = plasma concentration at time \(t\)
- \(D\) = administered dose
- \(V_d\) = apparent volume of distribution
- \(k\) = elimination rate constant
- \(t\) = time after administration

The elimination rate constant is:

\[
k=\frac{CL}{V_d}
\]

Where \(CL\) represents systemic clearance.

### 3.2 Two-compartment intravenous bolus model

The two-compartment model represents drug distribution between a central and a peripheral compartment.

The central compartment represents plasma and rapidly equilibrating tissues, while the peripheral compartment represents more slowly equilibrating tissues.

The model incorporates:

- Central volume of distribution (\(V_c\))
- Peripheral volume of distribution (\(V_p\))
- Systemic clearance (\(CL\))
- Intercompartmental clearance (\(Q\))

The compartmental drug amounts can be described by:

\[
\frac{dA_c}{dt}
=
-\frac{CL+Q}{V_c}A_c
+
\frac{Q}{V_p}A_p
\]

\[
\frac{dA_p}{dt}
=
\frac{Q}{V_c}A_c
-
\frac{Q}{V_p}A_p
\]

Where \(A_c\) and \(A_p\) represent the amounts of drug in the central and peripheral compartments, respectively.

The central plasma concentration is:

\[
C_c(t)=\frac{A_c(t)}{V_c}
\]

This model describes an initial distribution phase followed by a slower terminal elimination phase.

## 4. Population Pharmacokinetic Simulation

OpenPK-Twin extends individual pharmacokinetic modelling to virtual patient populations through Monte Carlo-based simulation.

The simulation introduces inter-individual variability in selected pharmacokinetic parameters, allowing users to investigate how differences in drug clearance and distribution influence concentration–time profiles.

The platform generates population-level summaries, including:

- Median concentration–time profile.
- 5th percentile concentration.
- 95th percentile concentration.
- Representative virtual patient profiles.

The percentile interval represents simulated population variability. It is not a confidence interval or a clinically validated therapeutic range.

## 5. Reproducibility

Reproducibility is an important design principle of OpenPK-Twin.

The simulation engine supports random seed configuration so that identical inputs and random seeds can reproduce identical numerical outputs within the tested computational environment.

Simulation exports preserve relevant metadata, including:

- Software name and version.
- Pharmacokinetic model.
- Administration route.
- Simulation completion timestamp.
- Input parameters.
- Model assumptions.

The project includes automated tests for both pharmacokinetic models, including same-seed reproducibility, different-seed population behaviour, and population percentile calculations.

Repeated one-compartment and two-compartment web simulations have also been compared using exported datasets.

## 6. Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| Numerical computation | NumPy |
| Scientific modelling | SciPy |
| Data visualization | Matplotlib |
| Backend framework | FastAPI |
| Data validation | Pydantic |
| ASGI server | Uvicorn |
| Frontend | React |
| Frontend tooling | Vite |
| Automated testing | Pytest |
| CI/CD | GitHub Actions |
| Backend deployment | Render |
| Frontend deployment | Vercel |

## 7. Installation and Local Development

### Requirements

- Python 3.10 or later.
- pip.
- Git.

### Clone the repository

```bash
git clone https://github.com/CodebreakerComeback/openpk-twin.git

cd openpk-twin
```

### Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**macOS / Linux**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

### Install the project

```bash
pip install --upgrade pip

pip install -e ".[dev]"
```

### Run automated tests

```bash
pytest -v
```

### Start the FastAPI backend

```bash
uvicorn openpk_twin.api.main:app --reload
```

The local API documentation will be available at:

http://127.0.0.1:8000/docs

## 8. REST API

OpenPK-Twin provides REST API endpoints for pharmacokinetic population simulation.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API information |
| GET | `/health` | Health check |
| POST | `/api/v1/population/iv-bolus` | One-compartment population simulation |
| POST | `/api/v1/population/two-compartment/iv-bolus` | Two-compartment population simulation |

Explore the API schemas, request parameters, and response structures through the interactive Swagger documentation:

https://openpk-twin-api.onrender.com/docs

## 9. Project Structure

```text
openpk-twin/
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── src/
│   └── openpk_twin/
│       ├── api/
│       ├── models/
│       ├── simulation/
│       └── visualization/
│
├── tests/
│   ├── test_api.py
│   ├── test_one_compartment.py
│   ├── test_population.py
│   ├── test_reproducibility.py
│   ├── test_two_compartment.py
│   └── test_visualization.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── index.html
│   └── package.json
│
├── LICENSE
├── README.md
├── pyproject.toml
└── render.yaml
```

## 10. Testing and Quality Assurance

OpenPK-Twin uses automated testing through GitHub Actions.

The continuous integration workflow currently tests the Python package across:

- Python 3.10
- Python 3.11
- Python 3.12
- Python 3.13
- Python 3.14

The test suite covers the pharmacokinetic models, population simulation, API functionality, visualization, and reproducibility.

The reproducibility test workflow has successfully passed across all five configured Python versions.

## 11. Current Project Status

**Version:** 0.1.0

**Development stage:** Early public release / research and educational use.

Currently implemented:

- One-compartment IV bolus modelling.
- Two-compartment IV bolus modelling.
- Virtual patient population simulation.
- Inter-individual variability configuration.
- Population concentration–time visualization.
- CSV export with reproducibility metadata.
- FastAPI backend and React frontend.
- Automated testing and reproducibility checks.
- Public deployment.

Further development will focus on expanding model capabilities, improving scientific validation, strengthening documentation, and supporting additional pharmacometric applications.

## 12. Intended Users

OpenPK-Twin is designed for:

- Pharmacy and Pharmaceutics students.
- Pharmacokinetic and pharmacometric researchers.
- Pharmaceutical scientists.
- Model-informed drug development learners.
- Computational pharmaceutical research groups.
- Open-source healthcare technology developers.

## 13. Scientific and Clinical Disclaimer

OpenPK-Twin is an educational and research-oriented computational toolkit.

The implemented models and simulated outputs have not been established as clinically validated for individual patient dosing or therapeutic decision-making.

The software is not a validated medical device and must not be used to make clinical dosing decisions or replace professional medical judgement.

Users are responsible for independently assessing model assumptions, parameter suitability, numerical accuracy, and limitations before using simulation results in scientific work.

## 14. Contributing

Contributions, bug reports, feature suggestions, code improvements, and scientific feedback are welcome.

Researchers and developers interested in improving pharmacokinetic modelling, population simulation, visualization, and computational reproducibility are encouraged to contribute.

Please open an issue before proposing major changes.

## 15. Licence

OpenPK-Twin is released under the MIT License.

See [LICENSE](LICENSE) for details.

## 16. Maintainer

**CodebreakerComeback**

GitHub: https://github.com/CodebreakerComeback
LinkedIn: https://www.linkedin.com/in/earuingam-gogoi-612768333

Built to connect pharmaceutical science with open-source computational research.

**OpenPK-Twin — Explore drug behaviour. Simulate virtual populations.**
