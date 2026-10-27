import time
import heapq
from typing import Dict, List, Tuple

from src.core.interfaces.search_engine_interface import ISearchEngine
from src.core.dtos.graph_dto import GraphDTO
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.search_response_dto import SearchResponseDTO
from src.core.dtos.search_state_dto import SearchStateDTO


class UniformCostSearch(ISearchEngine):

    def solve(self, graph: GraphDTO, request: SearchRequestDTO) -> SearchResponseDTO:
        start_time = time.perf_counter()

        start_visited = False
        if request.required_visit is None or request.start_node == request.required_visit:
            start_visited = True

        start_state = SearchStateDTO(
            current_node=request.start_node,
            visited_required=start_visited
        )

        # Priority Queue: (cost, tie_breaker, state, path)
        pq: List[Tuple[float, int, SearchStateDTO, List[str]]] = []
        tie_breaker = 0 # if 2 states have the same cost, we compare them with other elements in the tuple to avoid comparing SearchStateDTO objects directly
        heapq.heappush(pq, (0.0, tie_breaker, start_state, [request.start_node]))

        explored_costs: Dict[SearchStateDTO, float] = {} # stores the explored states and their minimum costs to reach them
        expanded_states = 0

        while pq: # while there are still states to explore
            current_cost, _, current_state, path = heapq.heappop(pq)

            # if we have already explored this state with a lower cost, we skip it
            if current_state in explored_costs and explored_costs[current_state] <= current_cost:
                continue
            # otherwise, we mark this state as explored with the current cost
            explored_costs[current_state] = current_cost
            expanded_states += 1

            # Verify if the current state is the goal state and if the required node has been visited
            if current_state.current_node == request.goal_node and current_state.visited_required:
                execution_ms = (time.perf_counter() - start_time) * 1000
                return SearchResponseDTO(
                    path=path,
                    total_cost=current_cost,
                    expanded_states_count=expanded_states,
                    execution_time_ms=execution_ms,
                    route_found=True,
                    call_guidance_required=False
                )

            # Get the neighbors of the current node, considering the user's profile and blocked edges
            raw_edges = graph.adjacency_list.get(current_state.current_node, [])

            for edge in raw_edges:
                if edge.edge_id in request.blocked_edges:
                    continue
                if request.profile.avoid_stairs and edge.has_stairs:
                    continue
                if request.profile.mode == "wheelchair" and not edge.wheelchair_accessible:
                    continue
                if request.profile.covered_only and not edge.is_covered:
                    continue

                new_cost = current_cost + edge.weight

                new_visited = current_state.visited_required
                if not new_visited and edge.target == request.required_visit:
                    new_visited = True

                next_state = SearchStateDTO(
                    current_node=edge.target,
                    visited_required=new_visited
                )

                if next_state not in explored_costs or new_cost < explored_costs[next_state]:
                    tie_breaker += 1
                    new_path = list(path)
                    new_path.append(edge.target)
                    heapq.heappush(pq, (new_cost, tie_breaker, next_state, new_path))

        # no path found to the goal node that satisfies the constraints
        execution_ms = (time.perf_counter() - start_time) * 1000
        call_guidance = request.profile.mode == "wheelchair"

        return SearchResponseDTO(
            path=[],
            total_cost=-1.0,
            expanded_states_count=expanded_states,
            execution_time_ms=execution_ms,
            route_found=False,
            call_guidance_required=call_guidance
        )