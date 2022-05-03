import json

from graphqlclient import GraphQLClient

SMASH_ULTIMATE_GAME_ID = 1386

SEEDING_TO_ROUNDS_FROM_FINAL = [1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193, 257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097]


class API:
    def __init__(self, token):
        self.client = GraphQLClient('https://api.smash.gg/gql/alpha')
        self.client.inject_token(f'Bearer {token}')

    def get_effective_seed(self, seed):
        prev_value = -1
        for index, value in enumerate(SEEDING_TO_ROUNDS_FROM_FINAL):
            if value == seed:
                return value
            if value >= seed:
                return prev_value

            prev_value = value

    def get_round_from_seed(self, seed):
        prev_index = -1
        for index, value in enumerate(SEEDING_TO_ROUNDS_FROM_FINAL):
            if value == seed:
                return index
            if value >= seed:
                return prev_index

            prev_index = index

    def get_seed_performance(self, expected, actual):
        expected_finish_round = self.get_round_from_seed(expected)
        actual_finish_round = self.get_round_from_seed(actual)

        return expected_finish_round - actual_finish_round

    def get_tournament_ultimate_standings(self, slug):
        r = self.client.execute('''
            query GetTournament($slug: String, $videogameId: [ID]) {
              tournament(slug: $slug) {
                name
                events(filter: {videogameId: $videogameId}) {
                    name
                    standings(query: {perPage: 100}) {
                        nodes {
                            entrant {
                                seeds {
                                    seedNum
                                    placement
                                    phase {
                                        phaseOrder
                                        name
                                    }
                                }
                                name
                            }
                            placement
                        }
                    }
                }
              }
            }
            ''',
            {
                "slug": slug,
                "videogameId": [SMASH_ULTIMATE_GAME_ID]
            })

        tournament_results = json.loads(r)["data"]["tournament"]

        custom_data = {
            "tournament_name": tournament_results["name"],
            "events": []
        }

        for event in tournament_results["events"]:
            event_json = {
                "event_name": event["name"],
                "standings": []
            }

            for standing in event["standings"]["nodes"]:
                correct_seed = None

                for seed in standing["entrant"]["seeds"]:
                    if seed["phase"]["phaseOrder"] == 1:
                        correct_seed = seed
                        break

                if len(standing["entrant"]["seeds"]) > 1:
                    print(f"More than one seed for {standing}")

                result = {
                    "name": standing["entrant"]["name"],
                    "seed": correct_seed["seedNum"],
                    "placement": standing["placement"]
                }

                result["performance"] = self.get_seed_performance(result["seed"], result["placement"])
                result["effectiveSeed"] = self.get_effective_seed(result["seed"])

                event_json["standings"].append({
                    "name": result["name"],
                    "performance": result["performance"],
                    "placement": result["placement"]
                })

            custom_data["events"].append(event_json)

        return custom_data
