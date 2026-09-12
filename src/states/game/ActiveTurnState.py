"""
ISPPV1 2023
Study Case: Ultimate Fantasy (RPG)

Author: Alejandro Mujica
alejandro.j.mujic4@gmail.com

This file contains the class ActiveTurnState: implements the Active Time /
Cooldown turn system where each battle entity accumulates rest time, and
the first entity to complete its rest time takes its turn.
"""

import math
import random
from typing import Any
import pygame
from gale.state import BaseState
from gale.timer import Timer
import settings


class ActiveTurnState(BaseState):
    """
    Manages battle turns dynamically based on entity rest/cooldown timers.
    """

    def enter(self, battle_state: Any) -> None:
        self.battle_state = battle_state

    def update(self, dt: float) -> None:
        """
        Updates rest timers for all living characters and enemies.
        The first entity to reach its rest_time gets its turn.
        """
        # Check victory condition
        if all(enemy.dead for enemy in self.battle_state.enemies):
            self._victory()
            return

        # Check defeat condition
        if all(char.dead for char in self.battle_state.party.characters.values()):
            self._faint()
            return

        # Gather all living entities (characters and enemies)
        living_characters = [
            c for c in self.battle_state.party.characters.values() if not c.dead
        ]
        living_enemies = [e for e in self.battle_state.enemies if not e.dead]

        all_entities = living_characters + living_enemies

        # Accumulate rest time for each entity
        for entity in all_entities:
            entity.current_rest += dt
            if hasattr(entity, "rest_bar") and entity.rest_bar is not None:
                entity.rest_bar.value = entity.current_rest

            if entity.current_rest >= entity.rest_time:
                # Entity has completed its rest time; trigger its turn
                entity.current_rest = 0.0
                if hasattr(entity, "rest_bar") and entity.rest_bar is not None:
                    entity.rest_bar.value = 0.0

                if entity in living_characters:
                    self._prompt_character_action(entity)
                else:
                    self._execute_enemy_turn(entity)
                return

    def _prompt_character_action(self, character: Any) -> None:
        """Prompts action selection for a character whose rest time completed."""
        from src.states.game.SelectActionState import SelectActionState

        def on_action_selected() -> None:
            if all(enemy.dead for enemy in self.battle_state.enemies):
                self._victory()

        self.state_machine.push(
            SelectActionState(self.state_machine),
            battle_state=self.battle_state,
            entity=character,
            on_action_selected=on_action_selected,
        )

    def _execute_enemy_turn(self, enemy: Any) -> None:
        """Executes an AI action for an enemy whose rest time completed."""
        from src.states.game.BattleMessageState import BattleMessageState

        action = random.choice(enemy.actions)

        if action["target_type"] == "enemy":
            targets = list(self.battle_state.party.characters.values())
            target_label = "you"
        else:
            targets = self.battle_state.enemies
            target_label = "them"

        if action["require_target"]:
            alive = [target for target in targets if not target.dead]
            if not alive:
                return
            target = random.choice(alive)
            amount = action["func"](enemy, target, action.get("strength"))
            settings.SOUNDS[action["sound_effect"]].play()
            Timer.tween(0.5, [(target.energy_bar, {"value": target.current_hp})])
            message = f"{enemy.name} used {action['name']} for {amount} HP on {target.name}."
        else:
            alive_targets = [target for target in targets if not target.dead]
            if not alive_targets:
                return
            amount = action["func"](enemy, alive_targets, action.get("strength"))
            settings.SOUNDS[action["sound_effect"]].play()

            for target in alive_targets:
                Timer.tween(0.5, [(target.energy_bar, {"value": target.current_hp})])

            message = (
                f"{enemy.name} used {action['name']} for {amount} HP on all of "
                f"{target_label}."
            )

        if all(character.dead for character in self.battle_state.party.characters.values()):
            self._faint()
            return

        self.state_machine.push(
            BattleMessageState(self.state_machine),
            battle_state=self.battle_state,
            message=message,
            on_close=lambda: None,
        )

    def _victory(self) -> None:
        """Triggers the victory sequence."""
        settings.stop_music("battle")
        self._victory_channel = settings.SOUNDS["victory"].play(loops=-1)

        from src.states.game.BattleMessageState import BattleMessageState

        self.state_machine.push(
            BattleMessageState(self.state_machine),
            battle_state=self.battle_state,
            message="Victory!",
            on_close=self._start_exp,
        )

    def _start_exp(self) -> None:
        total_level = sum(enemy.level for enemy in self.battle_state.enemies)
        num_characters = len(self.battle_state.party.characters)
        opponent_level = total_level / num_characters
        self._inc_exp(0, opponent_level)

    def _inc_exp(self, index: int, opponent_level: float) -> None:
        keys = sorted(self.battle_state.party.characters.keys())

        if index >= len(keys):
            self._fade_out()
            return

        character = self.battle_state.party.characters[keys[index]]

        if character.dead:
            self._inc_exp(index + 1, opponent_level)
            return

        exp = math.ceil(
            (character.hpiv + character.attackiv + character.defenseiv + character.magiciv)
            * opponent_level
        )

        from src.states.game.BattleMessageState import BattleMessageState

        self.state_machine.push(
            BattleMessageState(self.state_machine),
            battle_state=self.battle_state,
            message=f"{character.name} earned {exp} experience points!",
            on_close=None,
            can_input=False,
        )
        Timer.after(1.5, lambda: self._apply_exp(character, exp, index, opponent_level))

    def _apply_exp(
        self, character: Any, exp: int, index: int, opponent_level: float
    ) -> None:
        settings.SOUNDS["exp"].play()
        new_value = min(character.current_exp + exp, character.exp_to_level)
        Timer.tween(
            0.5,
            [(character.exp_bar, {"value": new_value})],
            on_finish=lambda: self._exp_applied(character, exp, index, opponent_level),
        )

    def _exp_applied(
        self, character: Any, exp: int, index: int, opponent_level: float
    ) -> None:
        self.state_machine.pop()
        character.current_exp += exp

        if character.current_exp >= character.exp_to_level:
            settings.SOUNDS["levelup"].play()
            character.current_exp -= character.exp_to_level
            last_level = character.level
            increases = character.level_up()
            hp_increase = increases[0]
            Timer.tween(
                0.5, [(character.energy_bar, {"value": character.current_hp - hp_increase})]
            )

            from src.states.game.BattleMessageState import BattleMessageState

            message = (
                f"Congratulations! {character.name} advanced from level "
                f"{last_level} to level {character.level}!"
            )
            self.state_machine.push(
                BattleMessageState(self.state_machine),
                battle_state=self.battle_state,
                message=message,
                on_close=lambda: self._show_stats(character, increases, index, opponent_level),
            )
        else:
            self._inc_exp(index + 1, opponent_level)

    def _show_stats(self, character: Any, increases: Any, index: int, opponent_level: float) -> None:
        from src.states.game.StatsMenuState import StatsMenuState

        self.state_machine.push(
            StatsMenuState(self.state_machine),
            character=character,
            stats=increases,
            on_close=lambda: self._inc_exp(index + 1, opponent_level),
        )

    def _fade_out(self) -> None:
        if self._victory_channel is not None:
            self._victory_channel.stop()

        from src.states.game.FadeInState import FadeInState
        from src.states.game.FadeOutState import FadeOutState

        if self.battle_state.final_boss:

            def on_complete() -> None:
                settings.SOUNDS["the-end"].play()
                self.state_machine.pop()
                self.state_machine.pop()

                from src.states.game.TheEndState import TheEndState

                self.state_machine.push(TheEndState(self.state_machine))
                self.state_machine.push(
                    FadeOutState(self.state_machine),
                    color=(0, 0, 0),
                    time=1,
                    on_complete=lambda: None,
                )

            self.state_machine.push(
                FadeInState(self.state_machine),
                color=(0, 0, 0),
                time=3,
                on_complete=on_complete,
            )
        else:

            def on_complete() -> None:
                self.state_machine.pop()
                self.state_machine.pop()
                self.state_machine.push(
                    FadeOutState(self.state_machine),
                    color=(255, 255, 255),
                    time=1,
                    on_complete=lambda: None,
                )

            self.state_machine.push(
                FadeInState(self.state_machine),
                color=(255, 255, 255),
                time=1,
                on_complete=on_complete,
            )

    def _faint(self) -> None:
        settings.stop_music("battle")
        settings.SOUNDS["game-over"].play()

        from src.states.game.FadeInState import FadeInState

        def on_complete() -> None:
            from src.states.game.GameOverState import GameOverState

            self.state_machine.push(GameOverState(self.state_machine))

        self.state_machine.push(
            FadeInState(self.state_machine),
            color=(0, 0, 0),
            time=1,
            on_complete=on_complete,
        )

    _victory_channel = None

    def render(self, surface: pygame.Surface) -> None:
        pass
