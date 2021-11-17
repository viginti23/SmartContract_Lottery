from scripts.deploy_lottery import deploy_lottery
from scripts.handy_funcs import LOCAL_BLOCKCHAIN_ENVIRONMENTS, fund_with_link, get_account, get_contract
from brownie import network
import pytest
import time


def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFeeInEth() + 1000000000})
    lottery.enter({"from": account, "value": lottery.getEntranceFeeInEth() + 1000000000})
    fund_with_link(lottery.address)
    lottery.endLottery({"from": account})
    time.sleep(180)
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
