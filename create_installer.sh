#!/bin/bash

# Simple Test App - Linux Installer Creator
set +e  # Don't exit on error

# Configuration
APP_NAME="SimpleTestApp"
APP_VERSION="1.0.0"
APP_DESCRIPTION="Simple Test Application with Update Mechanism"
MAINTAINER="Test Developer <test@example.com>"
ARCHITECTURE="amd64"
PYTHON_VERSION="3.8"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Check system
check_system() {
    log "Checking system compatibility..."
    
    if ! command -v python3 &> /dev/null; then
        warn "Python 3 not found, will be installed during package installation"
    fi
    
    if ! command -v dpkg-deb &> /dev/null; then
        error "dpkg-deb not found. Please install dpkg-dev"
        exit 1
    fi
    
    log "System check completed"
}

# Create directory structure
create_structure() {
    log "Creating package structure..."
    
    rm -rf build/ dist/ *.deb *.tar.gz
    
    mkdir -p build/${APP_NAME}-${APP_VERSION}
    mkdir -p build/${APP_NAME}-${APP_VERSION}/DEBIAN
    mkdir -p build/${APP_NAME}-${APP_VERSION}/opt/simple-test-app
    mkdir -p build/${APP_NAME}-${APP_VERSION}/usr/share/applications
    mkdir -p build/${APP_NAME}-${APP_VERSION}/usr/share/pixmaps
    mkdir -p build/${APP_NAME}-${APP_VERSION}/usr/bin
    mkdir -p build/${APP_NAME}-${APP_VERSION}/usr/share/doc/simple-test-app
    
    log "Directory structure created"
}

# Setup Python environment
setup_python_env() {
    log "Setting up Python environment..."
    
    python3 -m venv build/${APP_NAME}-${APP_VERSION}/opt/simple-test-app/venv || {
        warn "Failed to create virtual environment"
        return 1
    }
    
    source build/${APP_NAME}-${APP_VERSION}/opt/simple-test-app/venv/bin/activate || {
        warn "Failed to activate virtual environment"
        return 1
    }
    
    pip install --upgrade pip || warn "Failed to upgrade pip"
    pip install requests || warn "Failed to install requests"
    
    deactivate
    log "Python environment setup completed"
}

# Copy application files
copy_app_files() {
    log "Copying application files..."
    
    # Copy main files
    cp main.py build/${APP_NAME}-${APP_VERSION}/opt/simple-test-app/
    cp update_utils.py build/${APP_NAME}-${APP_VERSION}/opt/simple-test-app/
    
    # Create data directory
    mkdir -p build/${APP_NAME}-${APP_VERSION}/opt/simple-test-app/data
    
    log "Application files copied"
}

# Create launcher script
create_launcher() {
    log "Creating launcher script..."
    
    cat > build/${APP_NAME}-${APP_VERSION}/opt/simple-test-app/launcher.sh << 'EOF'
#!/bin/bash

APP_DIR="/opt/simple-test-app"
VENV_DIR="$APP_DIR/venv"

# Try to use virtual environment, fallback to system Python
if [ -d "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate" 2>/dev/null || {
        echo "Warning: Failed to activate virtual environment, using system Python"
        cd "$APP_DIR"
        python3 main.py "$@"
        exit $?
    }
fi

cd "$APP_DIR"
python3 main.py "$@"
EOF

    chmod +x build/${APP_NAME}-${APP_VERSION}/opt/simple-test-app/launcher.sh
    
    # Create system launcher
    cat > build/${APP_NAME}-${APP_VERSION}/usr/bin/simple-test-app << 'EOF'
#!/bin/bash
exec /opt/simple-test-app/launcher.sh "$@"
EOF

    chmod +x build/${APP_NAME}-${APP_VERSION}/usr/bin/simple-test-app
    
    log "Launcher script created"
}

# Create desktop entry
create_desktop_entry() {
    log "Creating desktop entry..."
    
    cat > build/${APP_NAME}-${APP_VERSION}/usr/share/applications/simple-test-app.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Simple Test App
Comment=Simple Test Application with Update Mechanism
Exec=/usr/bin/simple-test-app
Icon=simple-test-app
Terminal=false
Categories=Utility;Development;
StartupNotify=true
EOF

    # Create simple icon (text-based)
    cat > build/${APP_NAME}-${APP_VERSION}/usr/share/pixmaps/simple-test-app.xpm << 'EOF'
/* XPM */
static char * simple_test_app_xpm[] = {
"32 32 3 1",
" 	c None",
".	c #0000FF",
"+	c #FFFFFF",
"................................",
".++++++++++++++++++++++++++++++.",
".+                            +.",
".+    Simple Test App         +.",
".+                            +.",
".+    User Registration       +.",
".+    SQLite Database         +.",
".+    Update Mechanism        +.",
".+                            +.",
".+    Version 1.0.0           +.",
".+                            +.",
".++++++++++++++++++++++++++++++.",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................",
"................................"};
EOF
    
    log "Desktop entry created"
}

# Create DEBIAN control files
create_control_files() {
    log "Creating DEBIAN control files..."
    
    # Control file
    cat > build/${APP_NAME}-${APP_VERSION}/DEBIAN/control << EOF
Package: simple-test-app
Version: ${APP_VERSION}
Section: utils
Priority: optional
Architecture: ${ARCHITECTURE}
Depends: python3 (>= ${PYTHON_VERSION}), python3-tk, python3-pip
Maintainer: ${MAINTAINER}
Description: ${APP_DESCRIPTION}
 A simple desktop application for testing update mechanisms.
 Features user registration with SQLite database and automatic updates.
EOF

    # Post-installation script
    cat > build/${APP_NAME}-${APP_VERSION}/DEBIAN/postinst << 'EOF'
#!/bin/bash
set +e

echo "Configuring Simple Test App..."

# Set permissions
chown -R root:root /opt/simple-test-app || echo "Warning: Failed to set ownership"
chmod -R 755 /opt/simple-test-app || echo "Warning: Failed to set permissions"
chmod +x /opt/simple-test-app/launcher.sh || echo "Warning: Failed to make launcher executable"
chmod +x /usr/bin/simple-test-app || echo "Warning: Failed to make system launcher executable"

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || echo "Warning: Failed to update desktop database"
fi

echo "Simple Test App installation completed!"
echo "Run 'simple-test-app' or find it in your applications menu."

exit 0
EOF

    # Pre-removal script
    cat > build/${APP_NAME}-${APP_VERSION}/DEBIAN/prerm << 'EOF'
#!/bin/bash
set +e

echo "Preparing to remove Simple Test App..."

# Stop any running instances
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "simple-test-app" 2>/dev/null || true

exit 0
EOF

    # Post-removal script
    cat > build/${APP_NAME}-${APP_VERSION}/DEBIAN/postrm << 'EOF'
#!/bin/bash
set +e

if [ "$1" = "purge" ]; then
    echo "Purging Simple Test App data..."
    
    # Remove application directory
    if [ -d "/opt/simple-test-app" ]; then
        rm -rf /opt/simple-test-app || echo "Warning: Failed to remove application directory"
    fi
    
    # Update desktop database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database /usr/share/applications || echo "Warning: Failed to update desktop database"
    fi
fi

echo "Simple Test App removal completed."
exit 0
EOF

    # Make scripts executable
    chmod 755 build/${APP_NAME}-${APP_VERSION}/DEBIAN/postinst
    chmod 755 build/${APP_NAME}-${APP_VERSION}/DEBIAN/prerm
    chmod 755 build/${APP_NAME}-${APP_VERSION}/DEBIAN/postrm
    
    log "DEBIAN control files created"
}

# Create documentation
create_documentation() {
    log "Creating documentation..."
    
    cat > build/${APP_NAME}-${APP_VERSION}/usr/share/doc/simple-test-app/README << 'EOF'
Simple Test App
===============

A simple desktop application for testing update mechanisms.

Features:
- User registration with username and password
- SQLite database storage
- Automatic update checking
- Simple GUI interface

Usage:
------
Run 'simple-test-app' from the command line or find it in your applications menu.

The application will automatically check for updates on startup.

Files:
------
- Application: /opt/simple-test-app/
- Database: /opt/simple-test-app/data/users.db
- Launcher: /usr/bin/simple-test-app
EOF

    cat > build/${APP_NAME}-${APP_VERSION}/usr/share/doc/simple-test-app/changelog << EOF
simple-test-app (${APP_VERSION}) stable; urgency=medium

  * Initial release
  * User registration functionality
  * SQLite database integration
  * Automatic update mechanism
  * Simple GUI interface

 -- ${MAINTAINER}  $(date -R)
EOF

    gzip build/${APP_NAME}-${APP_VERSION}/usr/share/doc/simple-test-app/changelog || warn "Failed to compress changelog"
    
    log "Documentation created"
}

# Build DEB package
build_package() {
    log "Building DEB package..."
    
    # Calculate installed size
    INSTALLED_SIZE=$(du -sk build/${APP_NAME}-${APP_VERSION} | cut -f1)
    echo "Installed-Size: ${INSTALLED_SIZE}" >> build/${APP_NAME}-${APP_VERSION}/DEBIAN/control
    
    # Build package
    fakeroot dpkg-deb --build build/${APP_NAME}-${APP_VERSION} || {
        error "Failed to build DEB package"
        return 1
    }
    
    # Rename package
    mv build/${APP_NAME}-${APP_VERSION}.deb simple-test-app_${APP_VERSION}_${ARCHITECTURE}.deb || {
        error "Failed to rename package"
        return 1
    }
    
    log "DEB package built: simple-test-app_${APP_VERSION}_${ARCHITECTURE}.deb"
}

# Create source tarball for GitHub releases
create_source_tarball() {
    log "Creating source tarball..."
    
    mkdir -p dist/simple-test-app-${APP_VERSION}
    
    # Copy source files
    cp main.py dist/simple-test-app-${APP_VERSION}/
    cp update_utils.py dist/simple-test-app-${APP_VERSION}/
    cp create_installer.sh dist/simple-test-app-${APP_VERSION}/
    
    # Create install script for tarball
    cat > dist/simple-test-app-${APP_VERSION}/install.sh << 'EOF'
#!/bin/bash
set -e

echo "Installing Simple Test App..."

# Create installation directory
sudo mkdir -p /opt/simple-test-app
sudo mkdir -p /opt/simple-test-app/data

# Copy files
sudo cp main.py /opt/simple-test-app/
sudo cp update_utils.py /opt/simple-test-app/

# Create launcher
sudo tee /opt/simple-test-app/launcher.sh > /dev/null << 'LAUNCHER_EOF'
#!/bin/bash
cd /opt/simple-test-app
python3 main.py "$@"
LAUNCHER_EOF

sudo chmod +x /opt/simple-test-app/launcher.sh

# Create system launcher
sudo tee /usr/bin/simple-test-app > /dev/null << 'SYS_LAUNCHER_EOF'
#!/bin/bash
exec /opt/simple-test-app/launcher.sh "$@"
SYS_LAUNCHER_EOF

sudo chmod +x /usr/bin/simple-test-app

# Set permissions
sudo chown -R root:root /opt/simple-test-app
sudo chmod -R 755 /opt/simple-test-app

echo "Simple Test App installed successfully!"
echo "Run 'simple-test-app' to start the application."
EOF

    chmod +x dist/simple-test-app-${APP_VERSION}/install.sh
    
    # Create tarball
    cd dist
    tar -czf simple-test-app-${APP_VERSION}.tar.gz simple-test-app-${APP_VERSION}/
    cd ..
    
    log "Source tarball created: dist/simple-test-app-${APP_VERSION}.tar.gz"
}

# Create installation script
create_install_script() {
    log "Creating installation script..."
    
    cat > install.sh << 'EOF'
#!/bin/bash
set +e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INSTALL] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Find DEB package
DEB_FILE=$(ls simple-test-app_*.deb 2>/dev/null | head -n1)

if [ -z "$DEB_FILE" ]; then
    error "No Simple Test App DEB package found"
    exit 1
fi

log "Found package: $DEB_FILE"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    warn "Not running as root. You may be prompted for your password."
fi

# Install package
log "Installing Simple Test App..."

if command -v apt >/dev/null 2>&1; then
    sudo apt update || warn "Failed to update package lists"
    sudo apt install -y "./$DEB_FILE" || {
        warn "Failed with apt, trying dpkg"
        sudo dpkg -i "$DEB_FILE" || {
            warn "Failed with dpkg, trying to fix dependencies"
            sudo apt-get install -f -y || warn "Failed to fix dependencies"
        }
    }
elif command -v dpkg >/dev/null 2>&1; then
    sudo dpkg -i "$DEB_FILE" || {
        warn "Failed with dpkg, trying to fix dependencies"
        sudo apt-get install -f -y || warn "Failed to fix dependencies"
    }
else
    error "Neither apt nor dpkg found"
    exit 1
fi

log "Installation completed!"
log "Run 'simple-test-app' to start the application."
EOF

    chmod +x install.sh
    
    log "Installation script created: install.sh"
}

# Main function
main() {
    log "Starting Simple Test App installer creation..."
    
    check_system
    create_structure
    setup_python_env
    copy_app_files
    create_launcher
    create_desktop_entry
    create_control_files
    create_documentation
    build_package
    create_source_tarball
    create_install_script
    
    log "✅ Installer creation completed!"
    
    if [ -f "simple-test-app_${APP_VERSION}_${ARCHITECTURE}.deb" ]; then
        log ""
        log "Generated files:"
        log "  📦 simple-test-app_${APP_VERSION}_${ARCHITECTURE}.deb - DEB package"
        log "  📁 dist/simple-test-app-${APP_VERSION}.tar.gz - Source tarball for GitHub"
        log "  🚀 install.sh - Installation script"
        log ""
        log "To install locally:"
        log "  sudo ./install.sh"
        log ""
        log "To create GitHub release:"
        log "  1. Upload dist/simple-test-app-${APP_VERSION}.tar.gz to GitHub releases"
        log "  2. Tag the release as 'v${APP_VERSION}'"
    else
        error "Package creation failed"
        exit 1
    fi
}

# Run main function
main "$@"