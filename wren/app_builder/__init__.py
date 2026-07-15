"""Wren App Builder — turn a single prompt into a complete, deployable app.

Usage:
    oh build-app "a todo app with Firebase auth"
    oh build-web "my personal portfolio site"
    oh build-mobile "a fitness tracker with charts"
"""

from wren.app_builder.builder import AppBuilder, BuildResult

__all__ = ['AppBuilder', 'BuildResult']
