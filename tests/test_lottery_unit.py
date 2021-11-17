from brownie import Lottery, accounts, network, config, exceptions
from scripts.handy_funcs import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account, fund_with_link, get_contract
from scripts.deploy_lottery import deploy_lottery
from web3 import Web3
import pytest


def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    # deploy mocks which contain our starting USD/ETH conversion rate set by us manually
    # 4000 USD => 1 ETH
    # usdEntryFee = 50
    # 50/4000 = 0.0125
    expected_entrance_fee = Web3.toWei(0.0125, 'ether')
    entrance_fee = lottery.getEntranceFeeInEth()
    # Assert
    assert expected_entrance_fee == entrance_fee


def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act/assert
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter(
            {
                "from": get_account(),
                "value": lottery.getEntranceFeeInEth()
            }
        )


def test_can_start_and_enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery(
        {
            "from": account,
        }
    )
    lottery.enter(
        {
            "from": account,
            "value": lottery.getEntranceFeeInEth()
        }
    )
    assert lottery.players(0) == account


def test_can_end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()

    lottery = deploy_lottery()
    lottery.startLottery(
        {
            "from": account,
        }
    )
    fund_with_link(lottery.address)
    lottery.endLottery(
        {
            "from": account
        }
    )
    assert lottery.lottery_state() == 2  # CALCULATING WINNER state


def test_can_pick_winner_correctly():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    account = get_account()

    # Deploying lottery
    lottery = deploy_lottery()
    # Starting lottery
    lottery.startLottery(
        {
            "from": account,
        }
    )
    # Simulating multiple participants
    CONTESTANTS_NUMBER = 3
    for i in range(CONTESTANTS_NUMBER):
        lottery.enter(
            {
                "from": get_account(index=i),
                "value": lottery.getEntranceFeeInEth()
            }
        )
    # Funding the lottery contract with LINK for oracle fee
    fund_with_link(lottery.address)

    # Random number
    STATIC_RNG = 777
    expected_winner_index = 0  # STATIC_RNG % CONTESTANTS_NUMBER
    winner_account = get_account(index=expected_winner_index)

    starting_balance_of_winner_account = winner_account.balance()
    balance_of_lottery = lottery.balance()

    # Ending lottery: getting randomness, setting winner,
    # transferring balance to the winner, resetting lottery
    transaction = lottery.endLottery({"from": account})

    # Because we declared an event in the contract and we emitted it
    # within the endLottery function, we can access it through:
    request_id = transaction.events['RequestedRandomness']['requestId']

    # Mocking the transaction that is normally performed by VRF Coordinator
    # callBackWithRandomness eventually calls fulfillRandomness(requestId, randomness)
    get_contract('vrf_coordinator').callBackWithRandomness(
        request_id, STATIC_RNG, lottery.address, {
            "from": account
        })
    assert winner_account == lottery.recentWinner()
    assert lottery.balance() == 0
    assert winner_account.balance() == starting_balance_of_winner_account + balance_of_lottery
