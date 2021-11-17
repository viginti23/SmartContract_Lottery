from scripts.handy_funcs import get_account, get_contract, fund_with_link
from brownie import Lottery, network, config
import time


def deploy_lottery():
    account = get_account()
    lottery = Lottery.deploy(
        # address _priceFeedAddress
        get_contract('eth_usd_price_feed').address,
        # address _vrfCoordinator,
        get_contract('vrf_coordinator').address,
        # address _link,
        get_contract('link_token').address,
        # uint256 _fee,
        config['networks'][network.show_active()]['fee'],
        # bytes32 _keyhash
        config['networks'][network.show_active()]['keyhash'],
        {'from': account},
        publish_source=config['networks'][network.show_active()].get('verify', False)
    )
    print('Deploying lottery!')
    return lottery


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)
    print("The Lottery is started!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = lottery.getEntranceFeeInEth() + 100_000_000
    entering_tx = lottery.enter({"from": account, "value": value})
    entering_tx.wait(1)
    print("Entered the lottery!")


def end_lottery():
    """
    This function ends the lottery - chooses the winner but to do so,
    it needs to provide the contract with LINK tokens as well.
    """
    account = get_account()
    lottery = Lottery[-1]
    # Fund the contract
    funding_tx = fund_with_link(lottery.address)
    funding_tx.wait(1)
    # then end the lottery - endLottery calls requestRandomness
    # which then calls VRFCoordinator, which then calls fulfillRandomness back
    ending_tx = lottery.endLottery({"from": account})
    ending_tx.wait(1)
    # Waiting for the fulfillRandomness callback
    time.sleep(60)
    print(f"{lottery.recentWinner} is the winner!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
