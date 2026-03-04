# Transfer Instructions for [Project Name]

Replace `USER`, `CLUSTER`, and `PATH/TO/PROJECT` throughout.

## Transfer TO the cluster

```bash
# From your local machine:
rsync -avz --progress \
  data/ \
  pipeline/ \
  config.yaml \
  hpc/ \
  plan.approved \
  USER@CLUSTER:PATH/TO/PROJECT/
```

If the project uses containers, also transfer:
```bash
rsync -avz containers/ USER@CLUSTER:PATH/TO/PROJECT/containers/
```

## Verify transfer

```bash
ssh USER@CLUSTER "ls -lh PATH/TO/PROJECT/"
```

## Transfer BACK after completion

```bash
rsync -avz --progress \
  USER@CLUSTER:PATH/TO/PROJECT/results/ \
  results/
```

## Verify outputs after transfer back

```bash
bash hpc/verify_outputs.sh
```
