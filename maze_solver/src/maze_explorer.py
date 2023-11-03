import time
import requests
from collections import deque
import heapq
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress warnings related to self-signed SSL certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class MazeExplorer:
    def __init__(self, base_url):
        self.base_url = base_url

    def initialize_maze(self, user, maze_name):
        url = f"{self.base_url}/iniciar"
        data = {"id": user, "labirinto": maze_name}
        response = requests.post(url, json=data, verify=False)
        return response.json()

    def move(self, user, maze_name, new_position):
        url = f"{self.base_url}/movimentar"
        data = {"id": user, "labirinto": maze_name, "nova_posicao": new_position}
        response = requests.post(url, json=data, verify=False)
        return response.json()

    def validate_path(self, user, maze_name, all_movements):
        url = f"{self.base_url}/validar_caminho"
        data = {"id": user, "labirinto": maze_name, "todos_movimentos": all_movements}
        response = requests.post(url, json=data, verify=False)
        return response.json()

    def get_start_position(self, user, maze_name):
        graph = {}
        node = self.initialize_maze(user, maze_name)
        start_node = node['pos_atual']
        graph[start_node] = node['movimentos']
        return start_node, graph

    def explore_graph(self, user, maze_name, start_node, graph):
        start = start_node
        queue = []
        visited = set()
        queue.append(start_node)
        queue.extend(graph[start_node])
        visited.add(start_node)
        adjacent_nodes = graph[start_node]
        end = None
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            if node in visited and node not in queue:
                print(queue)
                continue
            if node not in adjacent_nodes:
                queue.append(node)
                continue
            print(f"\rExploring Maze ({maze_name}) -> (current node): [{node}]", end="")

            info = self.move(user, maze_name, node)
            visited.add(node)
            adjacent_nodes = info['movimentos']
            graph[node] = adjacent_nodes
            for vertex in adjacent_nodes:
                queue.append(vertex)
            if info['final']:
                end = node
                break
        return graph, start, end

    def bfs(self, graph, start, end):
        visited = set()
        queue = deque([(start, [start])])
        while queue:
            node, path = queue.popleft()
            if node == end:
                return path
            if node not in visited:
                visited.add(node)
                if node in graph:
                    for neighbor in graph[node]:
                        if neighbor not in visited:
                            queue.append((neighbor, path + [neighbor]))
        return None

    def astar(self, graph, start, end):
        open_list = []  # List of nodes to be explored
        closed_set = set()  # Set of nodes already explored
        parent_map = {}  # Maps each node to its parent in the path

        g_score = {node: float('inf') for node in graph}  # Current cost from start to each node
        g_score[start] = 0  # The cost from start to itself is 0

        f_score = {node: float('inf') for node in graph}  # Estimated total cost from start to end
        f_score[start] = self.heuristic(start, end)  # Estimated heuristic value

        heapq.heappush(open_list, (f_score[start], start))  # Add the start node to the open list

        while open_list:
            _, current = heapq.heappop(open_list)

            if current == end:
                return self.reconstruct_path(parent_map, current)

            closed_set.add(current)

            for neighbor in graph[current]:
                if neighbor in graph:
                    if neighbor in closed_set:
                        continue

                    tentative_g_score = g_score[current] + 1  # Distance between nodes is 1 (unweighted graph)

                    if tentative_g_score < g_score[neighbor]:
                        parent_map[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = g_score[neighbor] + self.heuristic(neighbor, end)
                        if neighbor not in open_list:
                            heapq.heappush(open_list, (f_score[neighbor], neighbor))

        return None

    def heuristic(self, node, end):
        # Simple heuristic: straight-line distance (can be customized)
        return abs(node - end)

    def reconstruct_path(self, parent_map, current):
        path = [current]
        while current in parent_map:
            current = parent_map[current]
            path.insert(0, current)
        return path

if __name__ == "__main__":
    base_url = "https://gtm.delary.dev"
    user = "grupo-m"
    maze_name = input("Insert Maze Name: ")

    explorer = MazeExplorer(base_url)
    start_position, graph_start = explorer.get_start_position(user, maze_name)

    graph, start, end = explorer.explore_graph(user=user, maze_name=maze_name, start_node=start_position, graph=graph_start)

    print(f"\nInitial point of the maze: {start}\nFinal point of the maze: {end}")
    
    start_time = time.time()
    path_bfs = explorer.bfs(graph=graph, start=start, end=end)
    end_time = time.time()
    
    print(f"Runtime (BFS): {end_time-start_time} seconds")
    
    if path_bfs:
        validation = explorer.validate_path(user, maze_name, path_bfs)
        print(validation)
        if validation["caminho_valido"]:
            print(f"Path found (BFS): {path_bfs}")
    else:
        print("No path found.")

    start_time = time.time()
    path_a_star = explorer.astar(graph=graph, start=start, end=end)
    end_time = time.time()
    
    print(f"Runtime (A*): {end_time-start_time} seconds")

    if path_a_star:
        validation = explorer.validate_path(user, maze_name, path_a_star)
        print(validation)
        if validation["caminho_valido"]:
            print(f"Path found (A*): {path_a_star}")
    else:
        print("No path found.")
