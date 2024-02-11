{
  description = "Workspace for the HuggingFace NLP course";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    devenv.url = "github:cachix/devenv";
    devenv.inputs.nixpkgs.follows = "nixpkgs";
    nix2container.url = "github:nlewo/nix2container";
    nix2container.inputs.nixpkgs.follows = "nixpkgs";
    mk-shell-bin.url = "github:rrbutani/nix-mk-shell-bin";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
  };

  nixConfig = {
    extra-substituters = [
      "https://devenv.cachix.org"
      "https://cuda-maintainers.cachix.org"
    ];

    extra-trusted-public-keys = [
      "devenv.cachix.org-1:w1cLUi8dv3hnoSPGAuibQv+f9TZLr6cv/Hm9XgU50cw="
      "cuda-maintainers.cachix.org-1:0dq3bujKpuEPMCX6U4WylrUDZ9JyUG0VpVZa7CNfq5E="
    ];
  };

  outputs = inputs@{ flake-parts, nixpkgs, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.devenv.flakeModule
      ];
      systems = [ "x86_64-linux" ];

      perSystem = { config, self', inputs', pkgs, system, ... }: {
        # This sets `pkgs` to a nixpkgs with allowUnfree option set.
        _module.args.pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
          config.allowBroken = true; # FIXME remove when farm-haystack is fixed
        };

        devenv.shells.default = {

          # imports = [
          #   # This is just like the imports in devenv.nix.
          #   # See https://devenv.sh/guides/using-with-flake-parts/#import-a-devenv-module
          #   # ./devenv-foo.nix
          # ];

          # https://devenv.sh/reference/options/
          languages.nix.enable = true;

          languages.python = {
            enable = true;
            package = (pkgs.python3.withPackages (ps: with ps; with pkgs.python3Packages; [
              cupy
              ijson
              jsonlines
              nltk
              # numpy
              # pip
              pytest
              # pytorch
              # scipy
              spacy
              tabulate
              # tqdm
            ]));
            venv = {
              enable = true;
              quiet = true;
              # Install the spacy pipeline locally
              requirements = ''
                https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl           
              '';
            };
          };

          services.elasticsearch.enable = true;

          packages = with pkgs; [
            curl
            noti
            wget
          ];

          scripts = {
            wikipedia_dl.exec = ''
              wget https://nlp.stanford.edu/projects/hotpotqa/enwiki-20171001-pages-meta-current-withlinks-processed.tar.bz2
              wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-page_props.sql.gz
              tar -xvf enwiki-20171001-pages-meta-current-withlinks-processed.tar.bz2
              mkdir -p $PROJECT_DIR/data/wikipedia/enwiki_whole
              mv enwiki-20171001-pages-meta-current-withlinks-processed/* $PROJECT_DIR/data/wikipedia/enwiki_whole/
              gzip -d enwiki-latest-page_props.sql.gz
              mkdir -p $PROJECT_DIR/data/wikipedia/enwiki_props
              mv enwiki-latest-page_props.sql $PROJECT_DIR/data/wikipedia/enwiki_props/
            '';

            techqa_dl.exec = ''
              wget -o $PROJECT_DIR/data/TechQA.tar.gz https://huggingface.co/datasets/PrimeQA/TechQA/resolve/main/TechQA.tar.gz
              (cd $PROJECT_DIR/data
              tar -xvf TechQA.tar.gz
              cd TechQA/technote_corpus/
              bzip2 -d full_technote_collection.txt.bz2)
            '';
          };


          # NIX_LD_LIBRARY_PATH = pkgs.makeLibraryPath [
          #   pkgs.stdenv.cc.cc
          #   pkgs.zlib
          # ];
          # NIX_LD = pkgs.fileContents "${pkgs.stdenv.cc}/nix-support/dynamic-linker";
          # buildInputs = [ pkgs.python311 ];

          enterShell = ''
            export PROJECT_DIR="`pwd`"
          '';
        };

      };
      flake = {
        # The usual flake attributes can be defined here, including system-
        # agnostic ones like nixosModule and system-enumerating ones, although
        # those are more easily expressed in perSystem.

      };
    };
}
