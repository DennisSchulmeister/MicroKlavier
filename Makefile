.PHONY: submodules-init submodules-pull tools clean

MPY_PORT=stm32
BOARD=PYBV11
LTO=1

# Initial fetch of all git submodules
submodules:
	echo ">>> Initializing and fetching submodules <<<"
	git submodule init
	git submodule update --recursive --remote

	cd lib/micropython; git fetch --all --tags --prune; git checkout tags/v1.19.1

## Pull and merge latest commits from all git submodules
#submodules-pull:
#	echo ">>> Pulling latest commits from all submodules <<<"
#	cd lib/micropython; git fetch; git merge origin/master;

# Build required micropython tools
tools:
	echo ">>> Building mpy-cross <<<"
	cd lib/micropython/mpy-cross; make

# Build new micropython firmare for the board
firmware:
	echo ">>> Building Micropython firmware <<<"
	cd lib/micropython/ports/$(MPY_PORT); make submodules; make BOARD=$(BOARD) LTO=$(LTO)

# Deploy firmware to the board
firmware-deploy:
	echo ">>> Deploying new firmware version to the board <<<"
	echo "Make sure to execute machine.bootloader() in the Microypthon REPL first"
	cd lib/micropython/ports/$(MPY_PORT); make deploy BOARD=$(BOARD)

# Clean all build files
clean:
	echo ">>> Cleaning previously built files <<<"
	cd lib/micropython/ports/$(MPY_PORT); make clean BOARD=$(BOARD)
