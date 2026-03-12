#!/bin/bash

#################################################
# SSL Certificate Generation Script
#################################################
# This script generates a self-signed SSL certificate
# for the Pulse-Chat server.
#
# What is being created:
# 1. Private Key (server.key): Secret key used to encrypt/decrypt data
# 2. Certificate (server.crt): Public certificate that identifies the server
#
# Self-signed certificates are suitable for development and testing,
# but for production, you should use certificates from a trusted CA.
#################################################

echo "==========================================="
echo "Generating SSL Certificates for Pulse-Chat"
echo "==========================================="
echo

# Check if OpenSSL is installed
if ! command -v openssl &> /dev/null; then
    echo "ERROR: OpenSSL is not installed."
    echo "Please install OpenSSL and try again."
    exit 1
fi

# Certificate details
COUNTRY="India"
STATE="Karnataka"
CITY="Bangalore"
ORG="Pulse-Chat"
UNIT="Development"
CN="localhost"              # Common Name - should match server hostname
DAYS=365                    # Certificate validity period

echo "Generating private key and self-signed certificate..."
echo

# Generate private key and certificate in one command
# -x509: Output a self-signed certificate instead of a certificate request
# -newkey rsa:2048: Generate a new RSA key with 2048-bit length
# -keyout: Output file for the private key
# -out: Output file for the certificate
# -days: Number of days the certificate is valid
# -nodes: Don't encrypt the private key (no password required)
# -subj: Certificate subject information
openssl req -x509 -newkey rsa:2048 \
    -keyout server.key \
    -out server.crt \
    -days $DAYS \
    -nodes \
    -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$UNIT/CN=$CN"

if [ $? -eq 0 ]; then
    echo
    echo "✓ Certificates generated successfully!"
    echo
    echo "Files created:"
    echo "  - server.key (Private Key)"
    echo "  - server.crt (Certificate)"
    echo
    echo "Certificate valid for $DAYS days"
    echo
    
    # Display certificate details
    echo "Certificate Informatio`n:"
    echo "------------------------"
    openssl x509 -in server.crt -noout -subject -dates
    echo
    
    # Set appropriate permissions (private key should be read-only by owner)
    chmod 600 server.key
    chmod 644 server.crt
    echo "Permissions set: server.key (600), server.crt (644)"
    echo
else
    echo
    echo "✗ Error generating certificates"
    exit 1
fi

echo "You can now start the server!"
