// SPDX-License-Identifier: MIT
pragma solidity ^0.8.21;

/**
 * Certificate Registry - Blockchain-based Certificate Verification
 * Allows institutions to issue certificates that cannot be forged
 * Anyone can verify certificates without centralized authority
 */

contract CertificateRegistry {
    
    // Certificate structure
    struct Certificate {
        address issuer;           // Who issued the certificate
        address recipient;        // Who received the certificate
        uint256 issuedAt;         // Timestamp of issuance
        string metadata;          // JSON metadata (student name, course, etc)
    }
    
    // Mapping of certificate hashes to certificate data
    mapping(bytes32 => Certificate) private certificates;
    
    // Array to track all certificate hashes (for listing)
    bytes32[] private certificateHashes;
    
    // Events
    event CertificateIssued(
        bytes32 indexed certHash,
        address indexed issuer,
        address indexed recipient,
        uint256 issuedAt,
        string metadata
    );
    
    event CertificateVerified(
        bytes32 indexed certHash,
        address verifier,
        uint256 verifiedAt
    );
    
    // Modifiers
    modifier validAddress(address _address) {
        require(_address != address(0), "Invalid address");
        _;
    }
    
    modifier validHash(bytes32 _hash) {
        require(_hash != bytes32(0), "Invalid hash");
        _;
    }
    
    // ==================== ISSUE CERTIFICATE ====================
    
    /**
     * Issue a new certificate to the blockchain
     * 
     * @param _certHash SHA256 hash of certificate (unique identifier)
     * @param _recipient Address of certificate recipient
     * @param _metadata JSON string containing certificate details
     */
    function issueCertificate(
        bytes32 _certHash,
        address _recipient,
        string memory _metadata
    ) public validAddress(_recipient) validHash(_certHash) {
        
        // Prevent overwriting existing certificates
        require(
            certificates[_certHash].issuedAt == 0,
            "Certificate already exists"
        );
        
        require(
            bytes(_metadata).length > 0,
            "Metadata cannot be empty"
        );
        
        // Create certificate
        certificates[_certHash] = Certificate({
            issuer: msg.sender,
            recipient: _recipient,
            issuedAt: block.timestamp,
            metadata: _metadata
        });
        
        // Track hash
        certificateHashes.push(_certHash);
        
        // Emit event
        emit CertificateIssued(
            _certHash,
            msg.sender,
            _recipient,
            block.timestamp,
            _metadata
        );
    }
    
    // ==================== RETRIEVE CERTIFICATE ====================
    
    /**
     * Get certificate details from blockchain
     * 
     * @param _certHash SHA256 hash of certificate
     * @return issuer Address that issued the certificate
     * @return recipient Address that received the certificate
     * @return issuedAt Timestamp of issuance
     * @return metadata JSON metadata
     */
    function getCertificate(bytes32 _certHash)
        public
        view
        validHash(_certHash)
        returns (
            address issuer,
            address recipient,
            uint256 issuedAt,
            string memory metadata
        )
    {
        Certificate memory cert = certificates[_certHash];
        
        return (
            cert.issuer,
            cert.recipient,
            cert.issuedAt,
            cert.metadata
        );
    }
    
    // ==================== VERIFY CERTIFICATE ====================
    
    /**
     * Check if a certificate has been issued
     * 
     * @param _certHash SHA256 hash of certificate
     * @return true if certificate exists, false otherwise
     */
    function isIssued(bytes32 _certHash)
        public
        view
        validHash(_certHash)
        returns (bool)
    {
        return certificates[_certHash].issuedAt != 0;
    }
    
    /**
     * Verify if a certificate belongs to a specific recipient
     * 
     * @param _certHash SHA256 hash of certificate
     * @param _recipient Address to verify against
     * @return true if certificate was issued to recipient
     */
    function verifyRecipient(bytes32 _certHash, address _recipient)
        public
        view
        validHash(_certHash)
        validAddress(_recipient)
        returns (bool)
    {
        Certificate memory cert = certificates[_certHash];
        return cert.recipient == _recipient && cert.issuedAt != 0;
    }
    
    /**
     * Get total number of issued certificates
     * 
     * @return Number of certificates in registry
     */
    function getTotalCertificates() public view returns (uint256) {
        return certificateHashes.length;
    }
    
    /**
     * Get certificate hash by index
     * 
     * @param _index Index in certificates array
     * @return Certificate hash at index
     */
    function getCertificateByIndex(uint256 _index)
        public
        view
        returns (bytes32)
    {
        require(_index < certificateHashes.length, "Index out of bounds");
        return certificateHashes[_index];
    }
    
    /**
     * Get all certificates issued by an address
     * Note: This is inefficient for large datasets; use events instead
     * 
     * @param _issuer Address of issuer
     * @return Array of certificate hashes
     */
    function getCertificatesByIssuer(address _issuer)
        public
        view
        validAddress(_issuer)
        returns (bytes32[] memory)
    {
        bytes32[] memory issuerCerts = new bytes32[](certificateHashes.length);
        uint256 count = 0;
        
        for (uint256 i = 0; i < certificateHashes.length; i++) {
            if (certificates[certificateHashes[i]].issuer == _issuer) {
                issuerCerts[count] = certificateHashes[i];
                count++;
            }
        }
        
        // Trim array to actual size
        bytes32[] memory result = new bytes32[](count);
        for (uint256 i = 0; i < count; i++) {
            result[i] = issuerCerts[i];
        }
        
        return result;
    }
    
    // ==================== REVOCATION (OPTIONAL) ====================
    
    // Mapping to track revoked certificates
    mapping(bytes32 => bool) private revoked;
    
    event CertificateRevoked(
        bytes32 indexed certHash,
        address revokedBy,
        uint256 revokedAt
    );
    
    /**
     * Revoke a certificate (only issuer can revoke)
     * 
     * @param _certHash SHA256 hash of certificate to revoke
     */
    function revokeCertificate(bytes32 _certHash)
        public
        validHash(_certHash)
    {
        require(
            certificates[_certHash].issuer == msg.sender,
            "Only issuer can revoke"
        );
        
        require(
            !revoked[_certHash],
            "Certificate already revoked"
        );
        
        revoked[_certHash] = true;
        
        emit CertificateRevoked(_certHash, msg.sender, block.timestamp);
    }
    
    /**
     * Check if certificate is revoked
     * 
     * @param _certHash SHA256 hash of certificate
     * @return true if revoked, false otherwise
     */
    function isRevoked(bytes32 _certHash)
        public
        view
        validHash(_certHash)
        returns (bool)
    {
        return revoked[_certHash];
    }
}
