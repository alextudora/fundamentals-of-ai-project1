import math
import time
import heapq
from typing import Dict, List, Tuple, Optional

from src.core.interfaces.search_engine_interface import ISearchEngine
from src.core.dtos.graph_dto import GraphDTO
from src.core.dtos.node_dto import NodeDTO
from src.core.dtos.search_request_dto import SearchRequestDTO
from src.core.dtos.search_response_dto import SearchResponseDTO
from src.core.dtos.search_state_dto import SearchStateDTO


class AStarSearch(ISearchEngine):

    def calculate_heuristic(
            self,
            current_node: str,
            goal_node: str,
            required_visit: Optional[str],
            visited_required: bool,
            nodes: Dict[str, NodeDTO]
    ) -> float:
        def get_travel_time(node_a_id: str, node_b_id: str) -> float:
            if node_a_id not in nodes or node_b_id not in nodes:
                return 0.0
            node_a = nodes[node_a_id]
            node_b = nodes[node_b_id]
            dx = node_a.x - node_b.x
            dy = node_a.y - node_b.y
            dz = node_a.z - node_b.z
            distance = math.sqrt(dx * dx + dy * dy + dz * dz) # Euclidean distance in 3D space
            return distance / 80.0 # Assuming an average walking speed of 80 meters per minute
        # If the required node has not been visited yet: h(S) = h(u -> R) + h(R -> goal), otherwise h(S) = h(u -> goal)
        if not visited_required and required_visit and required_visit in nodes:
            time_to_req = get_travel_time(current_node, required_visit)
            time_req_to_goal = get_travel_time(required_visit, goal_node)
            return time_to_req + time_req_to_goal

        return get_travel_time(current_node, goal_node)

    def solve(self, graph: GraphDTO, request: SearchRequestDTO) -> SearchResponseDTO:
        start_time = time.perf_counter()

        start_visited = False
        if request.required_visit is None or request.start_node == request.required_visit:
            start_visited = True

        start_state = SearchStateDTO(
            current_node=request.start_node,
            visited_required=start_visited
        )

        h_start = self.calculate_heuristic(
            request.start_node,
            request.goal_node,
            request.required_visit,
            start_visited,
            graph.nodes
        )
        # priority queue elements: (f_score, g_score, tie_breaker, state, path)
        # f_score = g_score + h_score, where g_score is the cost to reach the current state and h_score is the heuristic estimate to reach the goal from the current state
        pq: List[Tuple[float, float, int, SearchStateDTO, List[str]]] = []
        tie_breaker = 0
        heapq.heappush(pq, (h_start, 0.0, tie_breaker, start_state, [request.start_node]))

        # explored_costs keeps track of the minimum cost to reach each state. If we encounter a state with a higher cost than previously recorded, we skip it.
        explored_costs: Dict[SearchStateDTO, float] = {}
        expanded_states = 0

        while pq:
            f_score, g_score, _, current_state, path = heapq.heappop(pq) # extract the state with the lowest f_score from the priority queue

            if current_state in explored_costs and explored_costs[current_state] <= g_score:
                continue

            explored_costs[current_state] = g_score
            expanded_states += 1

            if current_state.current_node == request.goal_node and current_state.visited_required:
                execution_ms = (time.perf_counter() - start_time) * 1000
                return SearchResponseDTO(
                    path=path,
                    total_cost=g_score,
                    expanded_states_count=expanded_states,
                    execution_time_ms=execution_ms,
                    route_found=True,
                    call_guidance_required=False
                )

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

                # for every valid neighbor, the new g_score is the cost to reach the current state plus the cost of the edge to the neighbor
                new_g_score = g_score + edge.weight

                new_visited = current_state.visited_required
                if not new_visited and edge.target == request.required_visit:
                    new_visited = True

                next_state = SearchStateDTO(
                    current_node=edge.target,
                    visited_required=new_visited
                )

                # if new cost g(n) is less than the previously recorded cost for this state, we update the cost (calculate h(n), f(n) = g(n) + h(n)) and add it to the priority queue
                if next_state not in explored_costs or new_g_score < explored_costs[next_state]:
                    h_score = self.calculate_heuristic(
                        edge.target,
                        request.goal_node,
                        request.required_visit,
                        new_visited,
                        graph.nodes
                    )
                    f_score = new_g_score + h_score

                    tie_breaker += 1
                    new_path = list(path)
                    new_path.append(edge.target)
                    heapq.heappush(pq, (f_score, new_g_score, tie_breaker, next_state, new_path))

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