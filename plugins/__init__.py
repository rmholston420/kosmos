"""Kosmos plugin namespace.

Per ADR-007, plugins never import each other directly — all cross-plugin
coupling goes through the event bus or formal ports. This package is a
namespace only; it exposes no aggregated surface.
"""
