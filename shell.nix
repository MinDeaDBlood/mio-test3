{ pkgs ? import (fetchTarball "https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz") {
    config.allowUnfree = true;
  }
}:

let
  pythonWithTk = pkgs.python313.withPackages (ps: with ps; [
    pip
    tkinter
    requests
    exceptiongroup
  ]);

  fhsEnv = pkgs.buildFHSEnv {
    name = "mio-kitchen-fhs";

    targetPkgs = pkgs: (with pkgs; [
      pythonWithTk
      tcl
      tk
      pkg-config
      gcc
      gnumake
      liblzo
      libxcb
      xcb-proto
      libxcursor
      xorg.libX11
      zlib
      openssl
      libffi
      stdenv.cc.cc.lib
    ]);

    runScript = pkgs.writeShellScript "init-fhs.sh" ''
      export PYTHONPATH="${pythonWithTk}/lib/python3.13/site-packages:$PYTHONPATH"
      export TCL_LIBRARY="${pkgs.tcl}/lib/tcl${pkgs.tcl.version}"
      export TK_LIBRARY="${pkgs.tk}/lib/tk${pkgs.tk.version}"
      export PKG_CONFIG_PATH="${pkgs.liblzo}/lib/pkgconfig:$PKG_CONFIG_PATH"
      export C_INCLUDE_PATH="${pkgs.liblzo.dev}/include:$C_INCLUDE_PATH"
      export LIBRARY_PATH="${pkgs.liblzo}/lib:$LIBRARY_PATH"

      export VENV_DIR="$PWD/.venv"
      if [ ! -d "$VENV_DIR" ]; then
        python -m venv "$VENV_DIR"
      fi
      source "$VENV_DIR/bin/activate"
      python -m pip install --upgrade pip setuptools wheel
      python -m pip install -r requirements.txt

      PYTHON_VERSION=$(python --version)
      echo ""
      echo -e "\033[1;35m[FHS Container]\033[0m MIO Kitchen, \033[1;34m$PYTHON_VERSION\033[0m"
      export PS1="\n\[\033[1;35m\](FHS:mio-kitchen) \[\033[1;32m\]\u@\h\[\033[00m\]:\[\033[1;34m\]\w\[\033[00m\]\n$ "
      exec bash --norc
    '';
  };
in
pkgs.stdenv.mkDerivation {
  name = "mio-kitchen-fhs-shell";
  nativeBuildInputs = [ fhsEnv ];
  shellHook = ''
    exec ${fhsEnv}/bin/mio-kitchen-fhs
  '';
}
