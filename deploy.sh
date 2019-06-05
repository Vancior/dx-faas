echo $RSYNC_PASSWORD
while inotifywait -q -r ./edge/* ./web/* ./sdk/*; do
    rsync -arvz ./ hujuntao@219.224.171.217:/home/hujuntao/deploy/dx-proto --delete
done
