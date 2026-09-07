{
  description = "Development shell for openstrikers";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
        tools = with pkgs; [
          cmake ninja clang gcc gdb pkg-config just git curl wget
          python312 python312Packages.pip python312Packages.certifi
        ];
        libs = with pkgs; [
          alsa-lib libpulseaudio pipewire sndio jack2 dbus ibus systemd libusb1

          libGL libGLU libglvnd mesa vulkan-loader vulkan-headers libdrm
          libgbm egl-wayland

          libx11 libxext libxrandr libxcursor libxfixes libxi libxscrnsaver
          libxtst libxrender libxinerama wayland wayland-protocols libxkbcommon
          libdecor

          zstd bzip2 sdl3 sqlite fribidi libthai liburing
        ];
      in {
        devShells.default = pkgs.mkShell {
          packages = tools ++ libs;
          shellHook = ''
            export LD_LIBRARY_PATH=/run/opengl-driver/lib:${
              pkgs.lib.makeLibraryPath libs
            }:$LD_LIBRARY_PATH
          '';
        };
      }
    );
}
