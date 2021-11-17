from brownie import (
    network,
    accounts,
    config,
    Contract,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    interface
)
from web3 import Web3

LOCAL_BLOCKCHAIN_ENVIRONMENTS = ['development', 'ganache-local']
FORKED_BLOCKCHAIN_ENVIRONMENTS = ['mainnet-fork', 'mainnet-fork-dev']

DECIMALS = 8
STARTING_PRICE = 400_000_000_000  # 4000 USD + 8 decimals


def get_account(index=None, id=None):
    # accounts[0]
    # accounts.load("id")
    # accounts.add("env")
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
            or network.show_active() in FORKED_BLOCKCHAIN_ENVIRONMENTS):
        return accounts[0]  # pull from our development accounts
    return accounts.add(config['wallets']['from_key'])


# If we have no V3 contracts provided from the network, we deploy mocks
# Mapping mock name to the actual imported mock contract
contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """
    This function will grab the contract addresses from the brownie config if defined, otherwise, it will deploy
    a mock version of that contract, and return that mock contract.
        Args:
            contract name (string)
        Returns:
            brownie.network.contract.ProjectContract: the most recently deployed version of this contract
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            deploy_mocks()
        contract = contract_type[-1]
    else:
        contract_address = config['networks'][
            network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi)
    return contract


def deploy_mocks(decimals=DECIMALS, starting_price=STARTING_PRICE):
    print(f"The active network is {network.show_active()}")
    print("Deploying Mocks...")
    account = get_account()
    MockV3Aggregator.deploy(decimals, starting_price, {"from": get_account()})
    link_token = LinkToken.deploy({'from': account})
    vrf_coordinator = VRFCoordinatorMock.deploy(link_token.address, {'from': account})
    print('Mocks deployed!')


def fund_with_link(
        contract_address, account=None, link_token=None, amount=100_000_000_000_000_000):
    # 0.1 LINK - oracle transaction fee
    account = account if account else get_account()
    link_token = link_token if link_token else get_contract('link_token')
    tx = link_token.transfer(contract_address, amount, {'from': account})
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # link_token_contract.transfer(contract_address, amount, {"from": account})
    # link_token_contract.wait(1)
    tx.wait(1)
    print('Contract funded!')
    return tx
