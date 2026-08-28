{
   description = "Development shell for openstrikers";

   inputs = {
     nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
     flake-utils.url = "github:numtide/flake-utils";
   };

   outputs = { self, nixpkgs, flake-utils }:
     flake-utils.lib.eachDefaultSystem (system:
       let
         pkgs = import nixpkgs {
           inherit system;
         };
       in {
         devShells.default = pkgs.mkShell {
           packages = with pkgs; [
             python312
             python312Packages.pip
             python312Packages.certifi
             ninja
             git
             curl
             wget
             cmake
             clang
             gcc
             pkg-config
             just

             # audio
             alsa-lib
             libpulseaudio
             pipewire
             sndio
             jack2

             # X11
             xorg.libX11
             xorg.libXext
             xorg.libXrandr
             xorg.libXcursor
             xorg.libXfixes
             xorg.libXi
             xorg.libXScrnSaver
             xorg.libXtst
             xorg.libXinerama
             xorg.libXrender

             # Wayland
             wayland
             wayland-protocols
             libxkbcommon
             libdecor

             # grafica / GPU
             libGL
             libGLU
             mesa
             vulkan-loader
             vulkan-headers
             libdrm
             libgbm
             egl-wayland

             # varie
             dbus
             ibus
             systemd       # per libudev
             libusb1
             fribidi
             libthai
             liburing

             # per Aurora/Dawn
             zstd
             bzip2
             sdl3
             sqlite
           ];
         };
       });
 }
