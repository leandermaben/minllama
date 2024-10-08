from typing import Callable, Iterable, Tuple

import torch
from torch.optim import Optimizer


class AdamW(Optimizer):
    def __init__(
            self,
            params: Iterable[torch.nn.parameter.Parameter],
            lr: float = 1e-3,
            betas: Tuple[float, float] = (0.9, 0.999),
            eps: float = 1e-6,
            weight_decay: float = 0.0,
            correct_bias: bool = True,
    ):
        if lr < 0.0:
            raise ValueError("Invalid learning rate: {} - should be >= 0.0".format(lr))
        if not 0.0 <= betas[0] < 1.0:
            raise ValueError("Invalid beta parameter: {} - should be in [0.0, 1.0[".format(betas[0]))
        if not 0.0 <= betas[1] < 1.0:
            raise ValueError("Invalid beta parameter: {} - should be in [0.0, 1.0[".format(betas[1]))
        if not 0.0 <= eps:
            raise ValueError("Invalid epsilon value: {} - should be >= 0.0".format(eps))
        defaults = dict(lr=lr, betas=betas, eps=eps, weight_decay=weight_decay, correct_bias=correct_bias)
        super().__init__(params, defaults)

    def step(self, closure: Callable = None):
        loss = None
        if closure is not None:
            loss = closure()

        for group in self.param_groups:
            for p in group["params"]:
                if p.grad is None:
                    continue
                grad = p.grad.data
                if grad.is_sparse:
                    raise RuntimeError("Adam does not support sparse gradients, please consider SparseAdam instead")


                # State should be stored in this dictionary
                state = self.state[p]

                # Access hyperparameters from the `group` dictionary
                alpha = group["lr"]
                betas = group["betas"]
                # Update first and second moments of the gradients
                m = state["m"] if "m" in state else torch.zeros_like(grad)
                v = state["v"] if "v" in state else torch.zeros_like(grad)
                state["m"] = betas[0] * m + (1 - betas[0]) * grad
                state["v"] = betas[1] * v + (1 - betas[1]) * grad ** 2
                # Bias correction
                # Please note that we are using the "efficient version" given in
                # https://arxiv.org/abs/1412.6980
                t = state["t"] if "t" in state else 0
                state["t"] = t + 1
                alpha_t = alpha * (1 - betas[1] ** state["t"]) ** 0.5 / (1 - betas[0] ** state["t"])

                # Update parameters
                p.data = p.data - (alpha_t * state["m"] / (torch.sqrt(state["v"]) + group["eps"])+alpha * group["weight_decay"] * p.data)
                # Add weight decay after the main gradient-based updates.
                # Please note that the learning rate should be incorporated into this update.
                # p.data = p.data - alpha * group["weight_decay"] * p.data
        return loss