{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:

{
  env.GREET = "Artist Resolver Trackmanager";
  env.LD_LIBRARY_PATH = lib.makeLibraryPath (
    with pkgs;
    [ ]
  );

  packages = with pkgs; [ ];
  cachix.pull = [ "nix-linter" ];

  languages.python = {
    enable = true;
    version = "3.14";
    venv.enable = true;
    uv = {
      enable = true;
      sync.enable = true;
    };
  };

  env = {
  };

  enterShell = ''
    git --version
    python --version
    uv --version
  '';

}
