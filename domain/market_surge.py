import random

from constants import COMMODITIES
from domain.user_state import ANONYMOUS_USER_KEY

"""
directionBias: strength * 45%
20Bias: strength * 75%

strength: 0-1: net flow (buy - sell) and amount of players joined in
	trade pressure x player participation
	(net buy/sell)/(max(5000,total stock in play) x (players trading in stock)/(max(3,total players))


"""

MIN_UNITS_FOR_FULL_STRENGTH = 5000
# Participation uses this floor for small games; for larger games we use total named players.
MIN_PLAYERS_PARTICIPATION_DENOMINATOR = 3
MAX_DIRECTION_BIAS = 0.75
MAX_VALUE_20_BIAS = 0.75

ROLL_VALUES = (0.05, 0.10, 0.20)


def empty_flow_map() -> dict[str, int]:
    return {commodity: 0 for commodity in COMMODITIES}


def empty_participants_map() -> dict[str, list[str]]:
    return {commodity: [] for commodity in COMMODITIES}


def empty_participant_count_map() -> dict[str, int]:
    return {commodity: 0 for commodity in COMMODITIES}


def normalize_market_surge_enabled(raw) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.strip().lower() in {"1", "true", "yes", "on"}
    if isinstance(raw, (int, float)):
        return bool(raw)
    return False


def normalize_flow_map(raw) -> dict[str, int]:
    out = empty_flow_map()
    if not isinstance(raw, dict):
        return out
    for commodity in COMMODITIES:
        try:
            out[commodity] = int(raw.get(commodity, 0))
        except (TypeError, ValueError):
            out[commodity] = 0
    return out


def normalize_participants_map(raw) -> dict[str, list[str]]:
    out = empty_participants_map()
    if not isinstance(raw, dict):
        return out
    for commodity in COMMODITIES:
        users = raw.get(commodity, [])
        if not isinstance(users, list):
            continue
        seen = set()
        normalized = []
        for user in users:
            if not isinstance(user, str):
                continue
            name = user.strip()
            if not name or name in seen:
                continue
            seen.add(name)
            normalized.append(name)
        out[commodity] = normalized
    return out


def normalize_participant_count_map(raw) -> dict[str, int]:
    out = empty_participant_count_map()
    if not isinstance(raw, dict):
        return out
    for commodity in COMMODITIES:
        try:
            out[commodity] = max(0, int(raw.get(commodity, 0)))
        except (TypeError, ValueError):
            out[commodity] = 0
    return out


def ensure_market_surge_config(server) -> None:
    cfg = server.config
    cfg["MARKET_SURGE_ENABLED"] = normalize_market_surge_enabled(
        cfg.get("MARKET_SURGE_ENABLED")
    )
    cfg["TURN_NET_FLOW"] = normalize_flow_map(cfg.get("TURN_NET_FLOW"))
    cfg["NEXT_TURN_SURGE_FLOW"] = normalize_flow_map(cfg.get("NEXT_TURN_SURGE_FLOW"))
    cfg["TURN_STOCK_PARTICIPANTS"] = normalize_participants_map(
        cfg.get("TURN_STOCK_PARTICIPANTS")
    )
    cfg["NEXT_TURN_SURGE_PARTICIPANT_COUNT"] = normalize_participant_count_map(
        cfg.get("NEXT_TURN_SURGE_PARTICIPANT_COUNT")
    )


def record_trade(server, username: str, stock: str, signed_amount: int) -> None:
    if stock not in COMMODITIES or signed_amount == 0:
        return
    ensure_market_surge_config(server)
    flow_map = normalize_flow_map(server.config.get("TURN_NET_FLOW"))
    flow_map[stock] += int(signed_amount)
    server.config["TURN_NET_FLOW"] = flow_map

    if not username or username == ANONYMOUS_USER_KEY:
        return
    participants = normalize_participants_map(server.config.get("TURN_STOCK_PARTICIPANTS"))
    if username not in participants[stock]:
        participants[stock].append(username)
    server.config["TURN_STOCK_PARTICIPANTS"] = participants


def rotate_turn_state(server) -> None:
    ensure_market_surge_config(server)
    flow_map = normalize_flow_map(server.config.get("TURN_NET_FLOW"))
    participants = normalize_participants_map(server.config.get("TURN_STOCK_PARTICIPANTS"))
    server.config["NEXT_TURN_SURGE_FLOW"] = flow_map
    server.config["NEXT_TURN_SURGE_PARTICIPANT_COUNT"] = {
        commodity: len(participants.get(commodity, [])) for commodity in COMMODITIES
    }
    server.config["TURN_NET_FLOW"] = empty_flow_map()
    server.config["TURN_STOCK_PARTICIPANTS"] = empty_participants_map()


def _named_player_count(user_state) -> int:
    if not isinstance(user_state, dict):
        return 0
    count = 0
    for username, state in user_state.items():
        if username == ANONYMOUS_USER_KEY or not isinstance(state, dict):
            continue
        count += 1
    return count


def _stock_units_in_play(user_state, stock: str) -> int:
    if stock not in COMMODITIES or not isinstance(user_state, dict):
        return 0
    total_units = 0
    for username, state in user_state.items():
        if username == ANONYMOUS_USER_KEY or not isinstance(state, dict):
            continue
        stocks = state.get("stocks")
        if not isinstance(stocks, dict):
            continue
        try:
            total_units += max(0, int(stocks.get(stock, 0)))
        except (TypeError, ValueError):
            continue
    return total_units


def _surge_strength(
    net_flow: int, participant_count: int, total_players: int, units_for_full_strength: int
) -> float:
    denominator_units = max(int(units_for_full_strength), MIN_UNITS_FOR_FULL_STRENGTH)
    base_strength = min(abs(int(net_flow)) / float(denominator_units), 1.0)
    denominator = (
        int(total_players)
        if int(total_players) > MIN_PLAYERS_PARTICIPATION_DENOMINATOR
        else MIN_PLAYERS_PARTICIPATION_DENOMINATOR
    )
    participation_factor = min(max(int(participant_count), 0) / float(denominator), 1.0)
    return base_strength * participation_factor


def _normalize_roll_value(value: float) -> float:
    # Keep roll outcomes constrained to game-supported values only.
    return min(ROLL_VALUES, key=lambda x: abs(float(value) - x))


def _biased_roll_value(value: float, strength: float, aligned: bool) -> float:
    current = _normalize_roll_value(value)
    if not aligned or strength <= 0:
        return current
    if random.random() < (strength * MAX_VALUE_20_BIAS):
        return 0.20
    if current == 0.05 and random.random() < (strength * 0.35):
        return 0.10
    return current


def maybe_bias_roll(server, stock: str, action: str, value: float) -> tuple[str, float]:
    ensure_market_surge_config(server)
    if not server.config.get("MARKET_SURGE_ENABLED", False):
        return action, value
    if action not in ("Up", "Down"):
        return action, value

    flow_map = normalize_flow_map(server.config.get("NEXT_TURN_SURGE_FLOW"))
    participant_counts = normalize_participant_count_map(
        server.config.get("NEXT_TURN_SURGE_PARTICIPANT_COUNT")
    )
    net_flow = int(flow_map.get(stock, 0))
    if net_flow == 0:
        return action, value

    aligned_action = "Up" if net_flow > 0 else "Down"
    user_state = server.config.get("USER_STATE")
    total_players = _named_player_count(user_state)
    units_for_full_strength = _stock_units_in_play(user_state, stock)
    strength = _surge_strength(
        net_flow,
        participant_counts.get(stock, 0),
        total_players,
        units_for_full_strength,
    )
    if strength <= 0:
        return action, value

    resolved_action = action
    if action != aligned_action and random.random() < (strength * MAX_DIRECTION_BIAS):
        resolved_action = aligned_action

    resolved_value = _biased_roll_value(
        value,
        strength,
        aligned=(resolved_action == aligned_action),
    )
    return resolved_action, resolved_value
