#!/bin/bash
# QR Restaurant Ordering System - Run Script

cd "$(dirname "$0")"

echo "QR Restaurant Ordering System"
echo "=============================="
echo ""
echo "Admin Panel: http://localhost:5000/admin/"
echo "Kitchen:     http://localhost:5000/kitchen/login"
echo "Menu:        http://localhost:5000/scan/<qr_token>"
echo ""
echo "Default Admin: admin@restaurant.com / admin123"
echo ""

python wsgi.py
