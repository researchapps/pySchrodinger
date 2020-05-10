# pySchrodinger

This is an example of using [gridtest](https://github.com/vsoch/gridtest)
to provide testing and metric extraction for a small Python library,
represnted here, [jakevdp/pySchrodinger](https://github.com/jakevdp/pySchrodinger).
This library was selected as a strong use case for GridTest:

 1. A small library that doesn't have testing
 2. Research oriented
 3. A few functions or classes might be run over a grid of parameters to test
 4. Custom metrics would be useful to measure

Specifically, pySchrodinger is a Python solver for the 
1D Schrodinger equation.  See [jakevdp/pySchrodinger](https://github.com/jakevdp/pySchrodinger)
for the original code base. The remainder of this README will be used to describe
the complete process of starting with the original repository to add GridTest.

## Setting up GridTest

Gridtest can be installed via pip, or via conda (on conda-forge).

```bash
pip install gridtest
conda install --channel conda-forge gridtest
```

You would then want to generate your base testing file. Since our entire
module is represented in [schrodinger.py](schrodinger.py) we will run it
for that module. We will generate a gridtest.yml file, which is the default
that gridtest will discover.

```bash
gridtest generate schrodinger.py gridtest.yml
```

This gives us a basic template with the classes and functions to fill in:

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py
  tests:
    Schrodinger.compute_k_from_x:
    - args:
        self: null
    Schrodinger.compute_x_from_k:
    - args:
        self: null
    Schrodinger.solve:
    - args:
        Nsteps: 0.001
        dt: 1
        eps: 1000
        max_iter: null
    Schrodinger.time_step:
    - args:
        Nsteps: null
        dt: 1
    Schrodinger.wf_norm:
    - args:
        self: null
        wave_fn: null
    schrodinger.Schrodinger:
    - args:
        V_x: 1
        hbar: null
        k0: 0.0
        m: null
        psi_x0: 1
        t0: null
        x: null
```

Looking at the structure of the file, we see a single class that has more than
one function. 

## Create Your Grid

We can see from the above that the `schrodinger.Schrodinger` class can
create an instance, and the instance has functions like "solve" and "time_steps."
It looks like time steps is used to generate a simulation (animation), so for
our gridtests we only will care about:

 1. creating an instance over a grid of parameters
 2. running solve for that instance, with additional parameters for it

This means we can extensively use our delete key, and reduce the recipe
to the following:

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py
  tests:
    Schrodinger.solve:
    - args:
        Nsteps: 0.001
        dt: 1
        eps: 1000
        max_iter: null
    schrodinger.Schrodinger:
    - args:
        V_x: 1
        hbar: null
        k0: 0.0
        m: null
        psi_x0: 1
        t0: null
        x: null
```

Great! Now let's work on our grid. If you look at the file [animate_schrodinger.py](animate_schrodinger.py)
that was provided with the original repository, you get an idea of how the class is used.
There are a *bunch* of shared variables between the inputs to schrodinger.Schrodinger (for example,
psi_x0, V0, N, and x all go into different functions and should be consistent) and m is also
used in multiple places. If we were writing a script, we would go from top to bottom
and use common variables. How would this work to generate a parameter grid, and to
enture we don't use a psi_x0 that was calculated with a different N than was used
for the calculate of x? The answer is that we create functions that use a common parameter grid.
Let's add a grid to our yaml file now. Notice how we have args defined under each test?
We are going to move them up to the grid, and just tell the test to use it. First
we will just create the named grid `schrodinger_inputs` under grids, and copy paste
the arguments up there. This would technically be the same recipe, but now the
arguments are represented globally (and could be shared if needed).

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py
  grids:
    schrodinger_inputs
      args:
        V_x: 1
        hbar: null
        k0: 0.0
        m: null
        psi_x0: 1
        t0: null
        x: null

  tests:
    Schrodinger.solve:
    - args:
        Nsteps: 0.001
        dt: 1
        eps: 1000
        max_iter: null
    schrodinger.Schrodinger:
    - grid: schrodinger_inputs
```

## Create Your Functions

But we want the grid not for the globality, but for the ability to programatically
define inputs. For this step, I started with [animate_schrodinger.py](animate_schrodinger.py)
and created [schrodinger_helpers.py](schrodinger_helpers.py) to write a separate
function to define each input argument that was previously scattered in 
spaghetti code. For example, here you see the functions to generate x and psi_x0:

```python
def generate_psi_x0(N = 2 ** 11, dx = 0.1, V0 = 1.5, m=1.9):
    """generate the ps1_x0 variable for gridtest
    """
    # specify constants
    hbar = 1.0   # planck's constant

    # specify initial momentum and quantities derived from it
    p0 = np.sqrt(2 * m * 0.2 * V0)
    dp2 = p0 * p0 * 1. / 80
    d = hbar / np.sqrt(2 * dp2)
    x = generate_x(N, dx)

    L = hbar / np.sqrt(2 * m * V0)
    a = 3 * L
    x0 = -60 * L
    k0 = p0 / hbar

    # this is psi_x0
    return gauss_x(x, d, x0, k0)


def generate_x(N = 2 ** 11, dx = 0.1):
    """specify initial momentum and quantities derived from it
    """
    return dx * (np.arange(N) - 0.5 * N)
```

This also shows what we mentioned earlier - that arguments are shared! I wound up
writing the following functions:

 - generate_psi_x0 takes some inputs and returns `psi_x0`
 - generate_x takes some inputs and returns `x`
 - generate_V_x takes some inputs and returns `V_x`

## Add your Functions to the Grid

And so the next logical step was to add them to my grid! I will put them
under a "functions" section, and map each to it's corresponding variable.


```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py
  grids:
    schrodinger_inputs:
      args:
        m: null
      functions:
        V_x: schrodinger_helpers.generate_V_x
        x: schrodinger_helpers.generate_x
        psi_x0: schrodinger_helpers.generate_psi_x0

  tests:
    Schrodinger.solve:
    - args:
        Nsteps: 0.001
        dt: 1
        eps: 1000
        max_iter: null
    schrodinger.Schrodinger:
    - grid: schrodinger_inputs
```

We're almost done! Did you notice anything else? I also removed the variables V_x, x,
and psi_x0 from the args section of the grid, because they are returned by functions.
I also decided that h_bar (planck's constant), t0 (the initial time), and k0 
would either be set to reasonable defaults or be something constant and
not needed in the grid.

## Add Function Arguments

The grid is missing arguments that are intended for each function, so let's add them now.

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py
  grids:
    schrodinger_inputs:
      args:
        m: 1.9
        N: [512, 2048, 4096]
        dx: 1.5
        V0: 1.5
      functions:
        V_x: schrodinger_helpers.generate_V_x
        x: schrodinger_helpers.generate_x
        psi_x0: schrodinger_helpers.generate_psi_x0

  tests:
    Schrodinger.solve:
    - args:
        Nsteps: 0.001
        dt: 1
        eps: 1000
        max_iter: null
    schrodinger.Schrodinger:
    - grid: schrodinger_inputs
```

I chose the value of m (the particle mass) and dx and V0 to be similar to what I saw used in the example, and
decided that I would vary the value of N for the gridtest (the length of the array). I could remove the solve
function...

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py
  grids:
    schrodinger_inputs:
      args:
        m: 1.9
        N: [512, 2048, 4096]
        dx: 1.5
        V0: 1.5
      functions:
        V_x: schrodinger_helpers.generate_V_x
        x: schrodinger_helpers.generate_x
        psi_x0: schrodinger_helpers.generate_psi_x0

  tests:
    schrodinger.Schrodinger:
    - grid: schrodinger_inputs
```

and run the gridtest to see that we are running over three test cases (the matrix
generates 3 different parameter sets, which we can also check:

```bash
$ gridtest test tests.yml 
[3/3] |===================================| 100.0% 
Name                           Status                         Summary                       
________________________________________________________________________________________________________________________
schrodinger.Schrodinger.0      success                                                      
schrodinger.Schrodinger.1      success                                                      
schrodinger.Schrodinger.2      success                                                      

3/3 tests passed
```
```bash
$ gridtest gridview gridtest.yml
schrodinger_inputs

$ gridtest gridview gridtest.yml schrodinger_inputs --count
3 argument sets produced.
```

This is good to see, but not super interesting. We could add some boring checks,
like the instance returned is class Schrodinger, or a metric to see the result.

**Check creating instance**

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py
  grids:
    schrodinger_inputs:
      args:
        m: 1.9
        N: [512, 2048, 4096]
        dx: 1.5
        V0: 1.5
      functions:
        V_x: schrodinger_helpers.generate_V_x
        x: schrodinger_helpers.generate_x
        psi_x0: schrodinger_helpers.generate_psi_x0

  tests:
    schrodinger.Schrodinger:
    - grid: schrodinger_inputs
      isinstance: Schrodinger
```
```bash
$ gridtest test tests.yml 
[3/3] |===================================| 100.0% 
Name                           Status                         Summary                       
________________________________________________________________________________________________________________________
schrodinger.Schrodinger.0      success                        isinstance Schrodinger        
schrodinger.Schrodinger.1      success                        isinstance Schrodinger        
schrodinger.Schrodinger.2      success                        isinstance Schrodinger        

3/3 tests passed
```

**Add result metric**

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py
  grids:
    schrodinger_inputs:
      args:
        m: 1.9
        N: [512, 2048, 4096]
        dx: 1.5
        V0: 1.5
      functions:
        V_x: schrodinger_helpers.generate_V_x
        x: schrodinger_helpers.generate_x
        psi_x0: schrodinger_helpers.generate_psi_x0

  tests:
    schrodinger.Schrodinger:
    - grid: schrodinger_inputs
      isinstance: Schrodinger
      metrics: ["@result"]
```

Again, not super interesting.

```bash
$ gridtest test tests.yml 
[3/3] |===================================| 100.0% 
Name                           Status                         Summary                       
________________________________________________________________________________________________________________________
schrodinger.Schrodinger.0      success                        isinstance Schrodinger        
schrodinger.Schrodinger.1      success                        isinstance Schrodinger        
schrodinger.Schrodinger.2      success                        isinstance Schrodinger        

________________________________________________________________________________________________________________________
schrodinger.Schrodinger.0      @result                        <schrodinger.Schrodinger object at 0x7fe1ee7b88d0>
schrodinger.Schrodinger.1      @result                        <schrodinger.Schrodinger object at 0x7fe1ee7bf190>
schrodinger.Schrodinger.2      @result                        <schrodinger.Schrodinger object at 0x7fe1ee7bf110>

3/3 tests passed
```

## Add Solver Function

What we really care about is the solver (at least I think!) so let's write that
test now. Since we need an instantiated schrodinger.Schrodinger, let's just
name the one we already created and reference it. Note below that I've
named the instance `schrodinger_instance` and referened it as `self`
under the solver. I've also moved the result metric to be under solver,
because I think that's a more interesting thing to see.

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py

  grids:
    schrodinger_inputs:
      args:
        m: 1.9
        N: [512, 2048, 4096]
        dx: 1.5
        V0: 1.5
      functions:
        V_x: schrodinger_helpers.generate_V_x
        x: schrodinger_helpers.generate_x
        psi_x0: schrodinger_helpers.generate_psi_x0

  tests: 
    schrodinger.Schrodinger:
      - instance: schrodinger_instance
        grid: schrodinger_inputs
        isinstance: Schrodinger

    Schrodinger.solve:
    - args:
        self: "{{ instance.schrodinger_instance }}"
        Nsteps: 1
        dt: 1
        eps: 1000
        max_iter: 1000
      metrics: ["@result"]
```

Note that since we are providing an instance reference that is generated
over a grid, the solver will be tested over the same grid. We should see it run
three times, one for each instance.

```
$ gridtest test
[6/6] |===================================| 100.0% 
Name                           Status                         Summary                       
________________________________________________________________________________________________________________________
schrodinger.Schrodinger.0      success                        isinstance Schrodinger        
schrodinger.Schrodinger.1      success                        isinstance Schrodinger        
schrodinger.Schrodinger.2      success                        isinstance Schrodinger        
Schrodinger.solve.0            success                                                      
Schrodinger.solve.1            success                                                      
Schrodinger.solve.2            success                                                      

________________________________________________________________________________________________________________________
Schrodinger.solve.0            @result                        [ 0.00000000e+00+0.00000000e+00j  0.00000000e+00+0.00000000e+00j
Schrodinger.solve.1            @result                        [0.+0.j 0.+0.j 0.+0.j ... 0.+0.j 0.+0.j 0.+0.j]
Schrodinger.solve.2            @result                        [0.+0.j 0.+0.j 0.+0.j ... 0.+0.j 0.+0.j 0.+0.j]

6/6 tests passed
```

It might be more interesting to see the length of the result (and don't worry the
result will be kept with the data export) so let's add that.

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py

  grids:
    schrodinger_inputs:
      args:
        m: 1.9
        N: [512, 2048, 4096]
        dx: 1.5
        V0: 1.5
      functions:
        V_x: schrodinger_helpers.generate_V_x
        x: schrodinger_helpers.generate_x
        psi_x0: schrodinger_helpers.generate_psi_x0

  tests: 
    schrodinger.Schrodinger:
      - instance: schrodinger_instance
        grid: schrodinger_inputs
        isinstance: Schrodinger

    Schrodinger.solve:
    - args:
        self: "{{ instance.schrodinger_instance }}"
        Nsteps: 1
        dt: 1
        eps: 1000
        max_iter: 1000
      metrics: ["@length"]
```
```bash
$ gridtest test
[6/6] |===================================| 100.0% 
Name                           Status                         Summary                       
________________________________________________________________________________________________________________________
schrodinger.Schrodinger.0      success                        isinstance Schrodinger        
schrodinger.Schrodinger.1      success                        isinstance Schrodinger        
schrodinger.Schrodinger.2      success                        isinstance Schrodinger        
Schrodinger.solve.0            success                                                      
Schrodinger.solve.1            success                                                      
Schrodinger.solve.2            success                                                      

________________________________________________________________________________________________________________________
Schrodinger.solve.0            @length                        512                           
Schrodinger.solve.1            @length                        2048                          
Schrodinger.solve.2            @length                        4096                          

6/6 tests passed
```

This is great! What we see in 512, 2048, and 4096 are our values for N. Now we can 
parameterize the solver function to create a grid of results.

## Parameterize Solver Function

Let's keep it simple, and parameterize the variables dt and N_steps. We will first
add another argument set to schrodinger.Schrodinger.solver, but it will be considered
"inline" this time, meaning that we define args directly with the test.

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py

  grids:
    schrodinger_inputs:
      args:
        m: 1.9
        N: [512, 2048, 4096]
        dx: 1.5
        V0: 1.5
      functions:
        V_x: schrodinger_helpers.generate_V_x
        x: schrodinger_helpers.generate_x
        psi_x0: schrodinger_helpers.generate_psi_x0

  tests: 
    schrodinger.Schrodinger:
      - instance: schrodinger_instance
        grid: schrodinger_inputs
        isinstance: Schrodinger

    Schrodinger.solve:
    - args:
        self: "{{ instance.schrodinger_instance }}"
        Nsteps: [1, 2]
        dt: [0.01, 0.02]
        eps: 1000
        max_iter: 1000
      metrics: ["@length"]
```

We have added a small grid that would generate 2x2 or 4 results. Multiple that
by 3 (the number of instances) and we should see 12 results. And we do.

```bash
$ gridtest test
[15/15] |===================================| 100.0% 
Name                           Status                         Summary                       
________________________________________________________________________________________________________________________
schrodinger.Schrodinger.0      success                        isinstance Schrodinger        
schrodinger.Schrodinger.1      success                        isinstance Schrodinger        
schrodinger.Schrodinger.2      success                        isinstance Schrodinger        
Schrodinger.solve.0            success                                                      
Schrodinger.solve.1            success                                                      
Schrodinger.solve.2            success                                                      
Schrodinger.solve.3            success                                                      
Schrodinger.solve.4            success                                                      
Schrodinger.solve.5            success                                                      
Schrodinger.solve.6            success                                                      
Schrodinger.solve.7            success                                                      
Schrodinger.solve.8            success                                                      
Schrodinger.solve.9            success                                                      
Schrodinger.solve.10           success                                                      
Schrodinger.solve.11           success                                                      

________________________________________________________________________________________________________________________
Schrodinger.solve.0            @length                        512                           
Schrodinger.solve.1            @length                        512                           
Schrodinger.solve.2            @length                        512                           
Schrodinger.solve.3            @length                        512                           
Schrodinger.solve.4            @length                        2048                          
Schrodinger.solve.5            @length                        2048                          
Schrodinger.solve.6            @length                        2048                          
Schrodinger.solve.7            @length                        2048                          
Schrodinger.solve.8            @length                        4096                          
Schrodinger.solve.9            @length                        4096                          
Schrodinger.solve.10           @length                        4096                          
Schrodinger.solve.11           @length                        4096                          

15/15 tests passed
```

And just for kicks and giggles, let's add a metric to calculate time as well.

```yaml
schrodinger:
  filename: /home/vanessa/Desktop/Code/pySchrodinger/schrodinger.py

  grids:
    schrodinger_inputs:
      args:
        m: 1.9
        N: [512, 2048, 4096]
        dx: 1.5
        V0: 1.5
      functions:
        V_x: schrodinger_helpers.generate_V_x
        x: schrodinger_helpers.generate_x
        psi_x0: schrodinger_helpers.generate_psi_x0

  tests: 
    schrodinger.Schrodinger:
      - instance: schrodinger_instance
        grid: schrodinger_inputs
        isinstance: Schrodinger

    Schrodinger.solve:
    - args:
        self: "{{ instance.schrodinger_instance }}"
        Nsteps: [1, 2]
        dt: [0.01, 0.02]
        eps: 1000
        max_iter: 1000
      metrics: ["@length", "@timeit"]
```
```bash
$ gridtest test
[15/15] |===================================| 100.0% 
Name                           Status                         Summary                       
________________________________________________________________________________________________________________________
schrodinger.Schrodinger.0      success                        isinstance Schrodinger        
schrodinger.Schrodinger.1      success                        isinstance Schrodinger        
schrodinger.Schrodinger.2      success                        isinstance Schrodinger        
Schrodinger.solve.0            success                                                      
Schrodinger.solve.1            success                                                      
Schrodinger.solve.2            success                                                      
Schrodinger.solve.3            success                                                      
Schrodinger.solve.4            success                                                      
Schrodinger.solve.5            success                                                      
Schrodinger.solve.6            success                                                      
Schrodinger.solve.7            success                                                      
Schrodinger.solve.8            success                                                      
Schrodinger.solve.9            success                                                      
Schrodinger.solve.10           success                                                      
Schrodinger.solve.11           success                                                      

________________________________________________________________________________________________________________________
Schrodinger.solve.0            @length                        512                           
Schrodinger.solve.0            @timeit                        1.51 ms                       
Schrodinger.solve.1            @length                        512                           
Schrodinger.solve.1            @timeit                        1.49 ms                       
Schrodinger.solve.2            @length                        512                           
Schrodinger.solve.2            @timeit                        1.44 ms                       
Schrodinger.solve.3            @length                        512                           
Schrodinger.solve.3            @timeit                        1.57 ms                       
Schrodinger.solve.4            @length                        2048                          
Schrodinger.solve.4            @timeit                        5.19 ms                       
Schrodinger.solve.5            @length                        2048                          
Schrodinger.solve.5            @timeit                        3.94 ms                       
Schrodinger.solve.6            @length                        2048                          
Schrodinger.solve.6            @timeit                        5.06 ms                       
Schrodinger.solve.7            @length                        2048                          
Schrodinger.solve.7            @timeit                        4.94 ms                       
Schrodinger.solve.8            @length                        4096                          
Schrodinger.solve.8            @timeit                        9.41 ms                       
Schrodinger.solve.9            @length                        4096                          
Schrodinger.solve.9            @timeit                        9.40 ms                       
Schrodinger.solve.10           @length                        4096                          
Schrodinger.solve.10           @timeit                        7.14 ms                       
Schrodinger.solve.11           @length                        4096                          
Schrodinger.solve.11           @timeit                        7.06 ms                       

15/15 tests passed
```

Notice how we haven't doubled the tests, but we get a report of two metrics for each.


## Export Data

At this point, we might just want to run the grids, and then export our data to file.
We can do this as follows:

```bash
$ gridtest test gridtest.yml --save results.json
```

If you want the json to be compact, you can do:

```bash
gridtest test gridtest.yml --save results-compact.json --compact
```

And then the exported results could be used for analysis later, or used to
create a visualization. If you don't want to save a result for any particular test,
just add save: false to the test:

```yaml
  tests: 
    schrodinger.Schrodinger:
      - instance: schrodinger_instance
        grid: schrodinger_inputs
        isinstance: Schrodinger
        save: false
```
