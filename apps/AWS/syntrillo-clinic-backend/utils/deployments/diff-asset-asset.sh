if [ "$1" == "" -o "$2" == "" ]; then
    echo "usage: $0 asset_1  asset_2"
    exit
fi

arg_1=$(basename "$1" ".zip")
arg_2=$(basename "$2" ".zip")

asset_1="../../cdk.out/asset.$arg_1"
asset_2="../../cdk.out/asset.$arg_2"

echo $asset_1 $asset_2

diff -r $asset_1 $asset_2