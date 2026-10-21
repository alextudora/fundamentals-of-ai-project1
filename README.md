# Campus Route Planner — Fundamentals of AI Project 1

## 1. Project Overview

Campus Route Planner is an AI-based route-planning application designed to find paths between locations within a campus environment.

The system represents the campus as a graph in which nodes represent locations or points of interest (POIs), and edges represent connections between them. Each edge may have an associated travel cost and accessibility restrictions.

The project explores and compares two search algorithms:

- **Uniform Cost Search (UCS):** An exact baseline algorithm that finds a minimum-cost route when edge costs are non-negative.
- **A* Search:** An informed search algorithm that uses a heuristic to guide the search toward the destination.

The system aims to support route planning under different constraints, including accessibility requirements, blocked paths, geofencing restrictions, and required visits to specific locations.

## 2. Project Objectives

- Find minimum-cost routes between campus locations.
- Implement and compare UCS and A*.
- Support route restrictions and accessibility filters.
- Represent campus locations and points of interest.
- Handle unreachable destinations and invalid inputs.
- Support wheelchair-accessible route planning.
- Provide an alternative Call Guidance option when a valid route cannot be found.
- Evaluate algorithm correctness, performance, reliability, and safety limitations.

## 3. Technologies

The technologies used in the project include:

- **Programming Language:** Python
- **Search Algorithms:** Uniform Cost Search (UCS) and A*
- **Version Control:** Git and GitHub
- **Automated Testing:** Python testing framework
- **Continuous Integration:** GitHub Actions
- **Environment Management:** Python virtual environment and `requirements.txt`

Additional technologies for visualization or deployment will be documented as they are adopted by the team.

## 4. System Architecture

The project is organized around the following conceptual components:

- **Campus Graph:** Stores campus locations, connections, costs, and accessibility properties.
- **Route Search Engine:** Implements UCS and A*.
- **Restriction Management:** Applies blocked paths, accessibility filters, and geofencing constraints.
- **Route Validation:** Checks that generated paths satisfy the graph and route constraints.
- **User Interface:** Presents routes, points of interest, and relevant guidance.
- **Testing and Evaluation:** Validates correctness and compares search performance.
- **Reliability and Safety:** Supports reproducible execution, automated checks, risk documentation, and explicit system limitations.

The final implementation may differ from this conceptual architecture as development progresses.

## 5. Search Algorithms

### Uniform Cost Search (UCS)

UCS expands the lowest-cost unexplored state first. With non-negative edge costs, it finds a minimum-cost route when a solution exists and the search is implemented correctly.

### A* Search

A* prioritizes states according to:

`f(n) = g(n) + h(n)`

Where:

- `g(n)` is the cost accumulated from the starting node.
- `h(n)` is the estimated remaining cost to the destination.
- `f(n)` is the estimated total route cost through the current node.

For optimality, the heuristic and implementation must satisfy the relevant conditions. The heuristic must also be compatible with the edge-cost model.

## 6. Main Functional Requirements

The planned functionality includes:

- Route planning between campus locations.
- Search using UCS and A*.
- Support for blocked connections and route restrictions.
- Accessibility filtering for wheelchair users.
- Points of interest (POIs).
- Geofencing to restrict selections to the campus boundary.
- Required-visit or pickup constraints.
- Handling of unreachable destinations.
- Call Guidance as an alternative when no valid route is available.

Features should be marked as implemented only after they have been integrated and verified.

## 7. Reliability and Safety

The Reliability and Safety Officer focuses on the reproducibility and safe operation of the software within its defined limits.

### Development Environment

- Document the required Python version.
- Maintain project dependencies in `requirements.txt`.
- Provide consistent setup and execution instructions.
- Use a virtual environment or another documented environment-management method.

### Continuous Integration

GitHub Actions should run the automated test suite on relevant pushes and pull requests. Failed checks should be investigated before changes are considered ready to merge.

### Route Safety Checks

The system should verify that:

- A route uses valid graph connections.
- Blocked edges are not used.
- Wheelchair accessibility restrictions are respected when that profile is selected.
- Invalid or out-of-campus selections are rejected.
- Unreachable destinations are handled explicitly.
- Required-visit constraints are satisfied when applicable.

### System Boundaries and Limitations

The application operates on the campus graph and data provided to it. It cannot independently verify the real-world condition of a path, detect an unreported obstacle, or guarantee that a route is physically safe at the time of travel.

Accessibility and safety recommendations depend on the accuracy and completeness of the underlying data. The application should communicate these limitations clearly to users.

## 8. Testing and Evaluation

Testing should cover:

- Simple graphs with known optimal routes.
- Complex graphs with disconnected nodes.
- Blocked corridors and staircases.
- Wheelchair accessibility restrictions.
- Invalid graph data and negative edge costs.
- Out-of-campus selections.
- Required-visit constraints.
- Cases where no valid route exists.

UCS and A* should be compared using:

- Solution cost.
- Number of expanded states.
- Execution time in milliseconds.

Both algorithms should be evaluated on the same graph inputs and constraints. Performance results should be recorded from actual experiments rather than estimated.

## 9. Installation and Execution

### Prerequisites

- A compatible Python version.
- Git.
- A local copy of this repository.

### Setup

Clone the repository:

```bash
git clone <repository-url>
cd fundamentals-of-ai-project1
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies, if `requirements.txt` is available:

```bash
python -m pip install -r requirements.txt
```

Run the application and tests using the commands documented by the project maintainers. The exact entry point and test command should be added once the repository structure is finalized.

## 10. Repository Structure

The repository structure will be updated as modules are implemented. The project is expected to contain components for:

- Search algorithms.
- Campus graph and data.
- Route restrictions and accessibility.
- User interface and guidance.
- Automated tests and evaluation.
- Environment configuration and CI.
- Reliability and safety documentation.

## 11. Team Roles

- **Software Architect:** Defines the project architecture and component interfaces.
- **Product Owner:** Manages the backlog, priorities, and acceptance criteria.
- **AI Developer:** Implements UCS, A*, and route-search constraints.
- **Tester & Evaluator:** Develops test cases and evaluates algorithm correctness and performance.
- **Reliability & Safety Officer:** Supports reproducible development, CI configuration, system-boundary documentation, and verification of accessibility and geofencing constraints.

## 12. Academic Project Disclaimer

This project is developed for academic purposes as part of Fundamentals of AI Project 1.

Route recommendations depend on the accuracy, completeness, and freshness of the campus graph. The application does not independently inspect physical paths or guarantee real-world safety or accessibility.

Users should follow official campus instructions and verify relevant conditions when necessary.
