# Fisher-Bures Adversary Graph Convolutional Networks

[![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

This is a reference implementation of the paper [Fisher-Bures Adversary Graph Convolutional Networks](https://arxiv.org/abs/1903.04154).

## Outline

Based on information theory, the intrinsic shape of isotropic noise corresponds to the largest eigenvectors of the graph Laplacian. Such noise can bring a small but consistent improvement to generalization. In this paper, we discussed three different geometries of a graph that is embedded in a neural network, namely intrinsic geometry (how to define graph distance); extrinsic geometry (how perturbation of the graph affect the neural network); embedding geometry (how to measure graph embeddings). We imported new analytical tools from quantum information geometry into the domain of graph neural networks.

## Performance

The following table shows the average (20 random splits of train:dev:test data; 10 different random initialisations per split) testing loss/accuracy, based on a GCN model with one or two hidden layers, using a unified early stopping criterion. One can repeat these results using this [script](hpc/submit_grid.sh) (assuming one has access to HPC resources managed by [slurm](https://slurm.schedmd.com/documentation.html); otherwise one has to translate the script into actual commands). Notice that the scores have a large variation based on the how the train:dev:test datasets are selected (we use the same ratio as the Planetoid split [1]) and one has to be careful about this when comparing different GCN implementations.

| Model | Cora (2-layer) | CiteSeer (2-layer) | Pubmed (2-layer) | Cora (3-layer) | CiteSeer (3-layer) | Pubmed (3-layer)|
| --- | --- | --- | --- | --- | --- | --- |
| GCN |        1.07/80.52 | 1.36/69.59 | 0.75/78.17 | 0.93/79.16 | 1.31/67.68 | 0.89/76.65 |
| FisherGCN |  1.06/80.70 | 1.35/69.80 | 0.74/78.43 | 0.89/79.80 | 1.26/68.32 | 0.85/77.00 |
| GCNT |       1.04/81.20 | 1.33/70.31 | 0.70/78.99 | 0.87/80.40 | 1.29/68.28 | 0.79/78.11 |
| FisherGCNT | 1.03/81.46 | 1.32/70.48 | 0.69/79.34 | 0.84/80.85 | 1.24/68.67 | 0.76/78.50 |

The learning curves look like
![cora](data/lcurves/cora.svg)
![citeseer](data/lcurves/citeseer.svg)
![pubmed](data/lcurves/pubmed.svg)

## Requirements

- Python >= 3.6.x
- 1.13 <= Tensorflow < 2

Run
```
  pip install -r requirements.txt
```
to install all dependencies.

## Datasets

We use the same datasets as in [1][2][3]. They are stored in the folder [data](data/). Please [install](https://github.com/git-lfs/git-lfs/wiki/Installation) `git-lfs` before cloning the repository with the following commands

```bash
# ...install git-lfs...
git lfs install
git clone https://github.com/stellargraph/FisherGCN
```


## Run the code

```bash
python gcn/train.py --dataset <cora|citeseer|pubmed> --model <gcn|gcnT|fishergcn|fishergcnT> [--randomsplit NSPLIT] [--repeat REPEAT]
```
where NSPLIT is the number of random train:dev:test splits to run (use 0 for the default split),
and REPEAT is the number of random initialisations per split.
Check
```bash
python gcn/train.py --help
```
for more detailed parameter configurations.

## References

The following works are highlighted on which our codes and datasets are based. See our [paper](https://arxiv.org/abs/1903.04154) for the complete list of references.

[1] Zhilin Yang, William W. Cohen, Ruslan Salakhutdinov, [Revisiting Semi-Supervised Learning with Graph Embeddings](http://proceedings.mlr.press/v48/yanga16.html), ICML, 2016.

[2] Thomas N. Kipf, Max Welling, [Semi-Supervised Classification with Graph Convolutional Networks](https://arxiv.org/abs/1609.02907), ICLR, 2017.

[3] Oleksandr Shchur, Maximilian Mumme, Aleksandar Bojchevski, Stephan Günnemann, [Pitfalls of Graph Neural Network Evaluation](https://arxiv.org/abs/1811.05868), Relational Representation Learning Workshop, NIPS 2018.

## Cite

If you apply FisherGCN in your work, please cite

```
@inproceedings{fishergcn,
  author    = {Ke Sun and Piotr Koniusz and Zhen Wang},
  title     = {Fisher-Bures Adversary Graph Convolutional Networks},
  booktitle = {Uncertainty in Artificial Intelligence},
  year      = {2019},
  pages     = {161},
  note      = {arXiv:1903.04154 [cs.LG]},
  url       = {https://arxiv.org/abs/1903.04154},
}
```
