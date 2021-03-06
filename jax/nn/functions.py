# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Shared neural network activations and other functions."""


import numpy as onp

from jax import custom_jvp
from jax import dtypes
from jax import lax
from jax.scipy.special import expit
import jax.numpy as np

# activations

@custom_jvp
def relu(x):
  r"""Rectified linear unit activation function.

  Computes the element-wise function:

  .. math::
    \mathrm{relu}(x) = \max(x, 0)
  """
  return np.maximum(x, 0)
def _relu_jvp(primals, tangents):
  x, = primals
  t, = tangents
  return relu(x), lax.select(x > 0, t, lax.full_like(t, 0))
relu.defjvp(_relu_jvp)

def softplus(x):
  r"""Softplus activation function.

  Computes the element-wise function

  .. math::
    \mathrm{softplus}(x) = \log(1 + e^x)
  """
  return np.logaddexp(x, 0)

def soft_sign(x):
  r"""Soft-sign activation function.

  Computes the element-wise function

  .. math::
    \mathrm{soft\_sign}(x) = \frac{x}{|x| + 1}
  """
  return x / (np.abs(x) + 1)

def sigmoid(x):
  r"""Sigmoid activation function.

  Computes the element-wise function:

  .. math::
    \mathrm{sigmoid}(x) = \frac{1}{1 + e^{-x}}
  """
  return expit(x)

def swish(x):
  r"""Swish activation function.

  Computes the element-wise function:

  .. math::
    \mathrm{swish}(x) = x \cdot \mathrm{sigmoid}(x) = \frac{x}{1 + e^{-x}}
  """
  return x * sigmoid(x)

def log_sigmoid(x):
  r"""Log-sigmoid activation function.

  Computes the element-wise function:

  .. math::
    \mathrm{log\_sigmoid}(x) = \log(\mathrm{sigmoid}(x)) = -\log(1 + e^{-x})
  """
  return -softplus(-x)

def elu(x, alpha=1.0):
  r"""Exponential linear unit activation function.

  Computes the element-wise function:

  .. math::
    \mathrm{elu}(x) = \begin{cases}
      x, & x > 0\\
      \alpha \exp(x - 1), & x \le 0
    \end{cases}
  """
  safe_x = np.where(x > 0, 0., x)
  return np.where(x > 0, x, alpha * np.expm1(safe_x))

def leaky_relu(x, negative_slope=1e-2):
  r"""Leaky rectified linear unit activation function.

  Computes the element-wise function:

  .. math::
    \mathrm{leaky\_relu}(x) = \begin{cases}
      x, & x \ge 0\\
      \alpha x, & x < 0
    \end{cases}

  where :math:`\alpha` = :code:`negative_slope`.
  """
  return np.where(x >= 0, x, negative_slope * x)

def hard_tanh(x):
  r"""Hard :math:`\mathrm{tanh}` activation function.

  Computes the element-wise function:

  .. math::
    \mathrm{hard\_tanh}(x) = \begin{cases}
      -1, & x < -1\\
      x, & 0 \le x \le 1\\
      1, & 1 < x
    \end{cases}
  """
  return np.where(x > 1, 1, np.where(x < -1, -1, x))

def celu(x, alpha=1.0):
  r"""Continuously-differentiable exponential linear unit activation.

  Computes the element-wise function:

  .. math::
    \mathrm{celu}(x) = \begin{cases}
      x, & x > 0\\
      \alpha \exp(\frac{x}{\alpha} - 1), & x \le 0
    \end{cases}

  For more information, see
  `Continuously Differentiable Exponential Linear Units
  <https://arxiv.org/pdf/1704.07483.pdf>`_."""
  return np.where(x > 0, x, alpha * np.expm1(x / alpha))

def selu(x):
  r"""Scaled exponential linear unit activation.

  Computes the element-wise function:

  .. math::
    \mathrm{selu}(x) = \lambda \begin{cases}
      x, & x > 0\\
      \alpha e^x - \alpha, & x \le 0
    \end{cases}

  where :math:`\lambda = 1.0507009873554804934193349852946` and
  :math:`\alpha = 1.6732632423543772848170429916717`.

  For more information, see
  `Self-Normalizing Neural Networks
  <https://papers.nips.cc/paper/6698-self-normalizing-neural-networks.pdf>`_.
  """
  alpha = 1.6732632423543772848170429916717
  scale = 1.0507009873554804934193349852946
  return scale * elu(x, alpha)

def gelu(x):
  r"""Gaussian error linear unit activation function.

  Computes the element-wise function:

  .. math::
    \mathrm{gelu}(x) = \frac{x}{2} \left(1 + \mathrm{tanh} \left(
      \sqrt{\frac{2}{\pi}} \left(x + 0.044715 x^3 \right) \right) \right)

  We explicitly use the approximation rather than the exact formulation for
  speed. For more information, see `Gaussian Error Linear Units (GELUs)
  <https://arxiv.org/abs/1606.08415>`_, section 2.
  """
  sqrt_2_over_pi = onp.sqrt(2 / onp.pi).astype(x.dtype)
  cdf = 0.5 * (1.0 + np.tanh(sqrt_2_over_pi * (x + 0.044715 * x**3)))
  return x * cdf

def glu(x, axis=-1):
  """Gated linear unit activation function."""
  size = x.shape[axis]
  assert size % 2 == 0, "axis size must be divisible by 2"
  return x[..., :size] * sigmoid(x[..., size:])

# other functions

def log_softmax(x, axis=-1):
  r"""Log-Softmax function.

  Computes the logarithm of the :code:`softmax` function, which rescales
  elements to the range :math:`[-\infty, 0)`.

  .. math ::
    \mathrm{log\_softmax}(x) = \log \left( \frac{\exp(x_i)}{\sum_j \exp(x_j)}
    \right)

  Args:
    axis: the axis or axes along which the :code:`log_softmax` should be
      computed. Either an integer or a tuple of integers.
  """
  shifted = x - x.max(axis, keepdims=True)
  return shifted - np.log(np.sum(np.exp(shifted), axis, keepdims=True))

def softmax(x, axis=-1):
  r"""Softmax function.

  Computes the function which rescales elements to the range :math:`[0, 1]`
  such that the elements along :code:`axis` sum to :math:`1`.

  .. math ::
    \mathrm{softmax}(x) = \frac{\exp(x_i)}{\sum_j \exp(x_j)}

  Args:
    axis: the axis or axes along which the softmax should be computed. The
      softmax output summed across these dimensions should sum to :math:`1`.
      Either an integer or a tuple of integers.
  """
  unnormalized = np.exp(x - x.max(axis, keepdims=True))
  return unnormalized / unnormalized.sum(axis, keepdims=True)

def normalize(x, axis=-1, mean=None, variance=None, epsilon=1e-5):
  """Normalizes an array by subtracting mean and dividing by sqrt(var)."""
  if mean is None:
    mean = np.mean(x, axis, keepdims=True)
  if variance is None:
    # this definition is traditionally seen as less accurate than np.var's
    # mean((x - mean(x))**2) but may be faster and even, given typical
    # activation distributions and low-precision arithmetic, more accurate
    # when used in neural network normalization layers
    variance = np.mean(x**2, axis, keepdims=True) - mean**2
  return (x - mean) * lax.rsqrt(variance + epsilon)

def one_hot(x, num_classes, *, dtype=np.float64):
  """One-hot encodes the given indicies.

  Each index in the input ``x`` is encoded as a vector of zeros of length
  ``num_classes`` with the element at ``index`` set to one::

  >>> jax.nn.one_hot(np.array([0, 1, 2]), 3)
  DeviceArray([[1., 0., 0.],
               [0., 1., 0.],
               [0., 0., 1.]], dtype=float32)

  Indicies outside the range [0, num_classes) will be encoded as zeros::

  >>> jax.nn.one_hot(np.array([-1, 3]), 3)
  DeviceArray([[0., 0., 0.],
               [0., 0., 0.]], dtype=float32)

  Args:
    x: A tensor of indices.
    num_classes: Number of classes in the one-hot dimension.
    dtype: optional, a float dtype for the returned values (default float64 if
      jax_enable_x64 is true, otherwise float32).
  """
  dtype = dtypes.canonicalize_dtype(dtype)
  x = np.asarray(x)
  return np.array(x[..., np.newaxis] == np.arange(num_classes, dtype=x.dtype),
                  dtype=dtype)
