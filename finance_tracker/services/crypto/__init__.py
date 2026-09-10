"""Crypto rotation signal.

A rule engine that reads a portfolio and a market ranking and returns, per
position, one of five verdicts: hold, rotate into a ranked candidate, wait it
out in a stablecoin, take back the stake, or exit on a trailing stop.

It describes what has already happened. Nothing here forecasts a price, and
nothing here executes anything: every verdict is a proposal the user carries
out by hand, or does not.
"""
