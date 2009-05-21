

struct gc_generation {
	PyGC_Head head;
	int threshold; /* collection threshold */
	int count; /* count of allocations or collections of younger
		      generations */
};

#define NUM_GENERATIONS 3
#define GEN_HEAD(n) (&generations[n].head)

/* linked lists of container objects */
static struct gc_generation generations[NUM_GENERATIONS] = {
	/* PyGC_Head,				threshold,	count */
	{{{GEN_HEAD(0), GEN_HEAD(0), 0}},	700,		0},
	{{{GEN_HEAD(1), GEN_HEAD(1), 0}},	10,		0},
	{{{GEN_HEAD(2), GEN_HEAD(2), 0}},	10,		0},
};

PyGC_Head *_PyGC_generation0 = GEN_HEAD(0);

