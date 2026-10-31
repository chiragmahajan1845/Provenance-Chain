// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ProvenanceChain {
    enum Stage { Manufactured, InTransit, Warehoused, DeliveredToRetail, Sold }

    struct Checkpoint {
        Stage stage;
        string location;
        string metadataHash;
        address recordedBy;
        uint256 timestamp;
    }

    struct Product {
        string serialNumber;
        string name;
        string brand;
        address currentCustodian;
        Stage currentStage;
        bool isCounterfeitFlagged;
        string flagReason;
        uint256 checkpointCount;
    }

    address public owner;
    mapping(bytes32 => Product) public products;
    mapping(bytes32 => Checkpoint[]) private productCheckpoints;
    mapping(address => bool) public authorizedPartners;

    event ProductRegistered(bytes32 indexed productId, string serialNumber, string name, address indexed manufacturer);
    event CheckpointLogged(bytes32 indexed productId, Stage stage, string location, address indexed recordedBy, uint256 timestamp);
    event CounterfeitFlagged(bytes32 indexed productId, string reason, address indexed reporter);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner permitted");
        _;
    }

    modifier onlyAuthorized() {
        require(authorizedPartners[msg.sender] || msg.sender == owner, "Unauthorized actor");
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedPartners[msg.sender] = true;
    }

    function setPartnerAuthorization(address _partner, bool _status) external onlyOwner {
        authorizedPartners[_partner] = _status;
    }

    function generateProductId(string memory _serialNumber) public pure returns (bytes32) {
        return keccak256(abi.encodePacked(_serialNumber));
    }

    function registerProduct(
        string memory _serialNumber,
        string memory _name,
        string memory _brand,
        string memory _initialLocation,
        string memory _metadataHash
    ) external onlyAuthorized returns (bytes32) {
        bytes32 productId = generateProductId(_serialNumber);
        require(products[productId].checkpointCount == 0, "Duplicate serial: already registered");

        Product storage p = products[productId];
        p.serialNumber = _serialNumber;
        p.name = _name;
        p.brand = _brand;
        p.currentCustodian = msg.sender;
        p.currentStage = Stage.Manufactured;
        p.isCounterfeitFlagged = false;
        p.checkpointCount = 1;

        productCheckpoints[productId].push(Checkpoint({
            stage: Stage.Manufactured,
            location: _initialLocation,
            metadataHash: _metadataHash,
            recordedBy: msg.sender,
            timestamp: block.timestamp
        }));

        emit ProductRegistered(productId, _serialNumber, _name, msg.sender);
        return productId;
    }

    function logCheckpoint(
        bytes32 _productId,
        Stage _newStage,
        string memory _location,
        string memory _metadataHash,
        address _nextCustodian
    ) external onlyAuthorized {
        Product storage p = products[_productId];
        require(p.checkpointCount > 0, "Product not found");
        require(!p.isCounterfeitFlagged, "Product flagged as counterfeit");

        if (uint8(_newStage) <= uint8(p.currentStage)) {
            p.isCounterfeitFlagged = true;
            p.flagReason = "Anomaly: Out-of-order or duplicate stage update";
            emit CounterfeitFlagged(_productId, p.flagReason, msg.sender);
            return;
        }

        if (uint8(_newStage) > uint8(p.currentStage) + 1) {
            p.isCounterfeitFlagged = true;
            p.flagReason = "Anomaly: Skipped required milestone";
            emit CounterfeitFlagged(_productId, p.flagReason, msg.sender);
            return;
        }

        p.currentStage = _newStage;
        if (_nextCustodian != address(0)) {
            p.currentCustodian = _nextCustodian;
        }
        p.checkpointCount += 1;

        productCheckpoints[_productId].push(Checkpoint({
            stage: _newStage,
            location: _location,
            metadataHash: _metadataHash,
            recordedBy: msg.sender,
            timestamp: block.timestamp
        }));
    }

    function getProduct(bytes32 _productId) external view returns (Product memory) {
        return products[_productId];
    }

    function getHistory(bytes32 _productId) external view returns (Checkpoint[] memory) {
        return productCheckpoints[_productId];
    }
}
