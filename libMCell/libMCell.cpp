/* File : libMCell.cpp */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <math.h>

#include <iostream>
#include <string>
#include <vector>

#include "StorageClasses.h"
#include "libMCell.h"

#include "rng.h"

using namespace std;

int MCellSimulation::num_simulations = 0;

char *MCellSimulation::join_path ( char *p1, char sep, char *p2 ) {
  char *joined_path;
  if ((p1 == NULL) && (p2 == NULL) ) {
    joined_path = NULL;
  } else if ((p2 == NULL) || (strlen(p2) == 0) ) {
    joined_path = (char *) malloc ( strlen(p1) + 1 );
    strcpy ( joined_path, p1 );
  } else if ((p1 == NULL) || (strlen(p1) == 0) ) {
    joined_path = (char *) malloc ( strlen(p2) + 1 );
    strcpy ( joined_path, p2 );
  } else {
    joined_path = (char *) malloc ( strlen(p1) + 1 + strlen(p2) + 1 );
    strcpy ( joined_path, p1 );
    joined_path[strlen(p1)] = '/';
    strcpy ( &joined_path[strlen(p1)+1], p2 );
  }
  return ( joined_path );
}

void MCellSimulation::add_molecule_species ( MCellMoleculeSpecies *species ) {
  molecule_species[species->name.c_str()] = species;
}

void MCellSimulation::add_molecule_release_site ( MCellReleaseSite *site ) {
  molecule_release_sites.append ( site );
}

MCellMoleculeSpecies *MCellSimulation::get_molecule_species_by_name ( char *mol_name ) {
  MCellMoleculeSpecies *found = NULL;
  found = this->molecule_species[mol_name];
  return ( found );
}

/*
void MCellSimulation::pick_displacement( MCellMoleculeInstance *mol, double scale, struct rng_state *rng ) {
  mol->x = scale * rng_gauss(rng) * .70710678118654752440;
  mol->y = scale * rng_gauss(rng) * .70710678118654752440;
  mol->z = scale * rng_gauss(rng) * .70710678118654752440;
}
*/

void MCellSimulation::run_simulation ( char *proj_path ) {
  int iteration;

  printf ( "Project path = \"%s\"\n", proj_path );

  // ##### Clear out the old data

  printf ( "Creating directories ...\n" );

  char *react_dir = join_path ( proj_path, '/', "react_data" );
  mkdir ( react_dir, 0777 );

  char *viz_dir = join_path ( proj_path, '/', "viz_data" );
  mkdir ( viz_dir, 0777 );

  char *viz_seed_dir = join_path ( viz_dir, '/', "seed_00001" );
  mkdir ( viz_seed_dir, 0777 );


  printf ( "Generating Data ...\n" );


  // # Create structures and instances for each molecule that is released (note that release patterns are not handled)

  MCellReleaseSite *this_site;

  for (int rs_num=0; rs_num<this->molecule_release_sites.get_size(); rs_num++) {
    cout << "Release Site " << rs_num << endl;
    this_site = this->molecule_release_sites[rs_num];
    cout << "  Releasing " << this_site->quantity << " molecules of type " << this_site->molecule_species->name << endl;
    for (int i=0; i<this_site->quantity; i++) {
      // cout << "  Releasing a molecule of type " << this_site->molecule_species->name << endl;
      MCellMoleculeInstance *new_mol_instance = new MCellMoleculeInstance();
      new_mol_instance->next = this_site->molecule_species->instance_list;
      this_site->molecule_species->instance_list = new_mol_instance;
      this_site->molecule_species->num_instances += 1;
      new_mol_instance->molecule_species = this_site->molecule_species;
      new_mol_instance->x = this_site->x;
      new_mol_instance->y = this_site->y;
      new_mol_instance->z = this_site->z;
    }
  }

  // # Figure out the number of digits needed for file names and allocate strings as file name templates

  int ndigits = 1 + log10(num_iterations+1);
  printf ( "File names will require %d digits\n", ndigits );
  char *template_template = "seed_00001/Scene.cellbin.%%0%dd.dat";
  char *file_template = (char *) malloc ( strlen(template_template) + (ndigits*sizeof(char)) + 10 );
  sprintf ( file_template, template_template, ndigits );
  printf ( "File Template = %s\n", file_template );

  char *f_template =  (char *) malloc ( ( strlen(viz_dir) + 1 + strlen(file_template) + ndigits + 10 ) *sizeof(char));
  sprintf ( f_template, "%s/%s", viz_dir, file_template );
  printf ( "Full Template = %s\n", f_template );

  char *sim_step_mol_name = (char *) malloc ( strlen(f_template) + 10 );

  // Run the actual simulation
  printf ( "Begin libMCell simulation (printf).\n" );
  cout << "Begin libMCell simulation (cout)." << endl;
  
  MCellRandomNumber_mrng *mcell_random = new MCellRandomNumber_mrng((uint32_t)12345);

  int print_every = exp10(floor(log10((num_iterations/10))));
  if (print_every < 1) print_every = 1;
  for (iteration=0; iteration<=num_iterations; iteration++) {
    cout << "Iteration " << iteration << ", t=" << (time_step*iteration) << endl;

    sprintf ( sim_step_mol_name, f_template, iteration );
    if ((iteration%print_every) == 0) {
      printf ( "Creating mol viz file: \"%s\"\n", sim_step_mol_name );
    }
    FILE *f = fopen ( sim_step_mol_name, "w" );
    // Write the binary marker for this file
    int binary_marker = 1;
    fwrite ( &binary_marker, sizeof(int), 1, f );

    MCellMoleculeSpecies *this_species;
    cout << "Iterate over " << this->molecule_species.get_num_items() << " species." << endl;
    for (int sp_num=0; sp_num<this->molecule_species.get_num_items(); sp_num++) {
      this_species = this->molecule_species[this->molecule_species.get_key(sp_num)];
      cout << "Simulating for species " << this_species->name << endl;

      unsigned char name_len = 0x0ff & this_species->name.length();
      fwrite ( &name_len, sizeof(unsigned char), 1, f );
      fwrite ( this_species->name.c_str(), sizeof(unsigned char), this_species->name.length(), f );
      unsigned char type_code = 0x0ff & (int)(this_species->type_code);
      fwrite ( &type_code, sizeof(unsigned char), 1, f );
      int total_values = 3 * this_species->num_instances;
      fwrite ( &total_values, sizeof(int), 1, f );

      MCellMoleculeInstance *this_mol_instance = this_species->instance_list;
      float float_val;
      double dc = this_species->diffusion_constant;
      // From one branch of mcell_species.c ...  Determine the actual space step and time step
      double ds = sqrt(16.0 * 1.0e8 * dc * time_step);


      while (this_mol_instance != NULL) {
        float_val = this_mol_instance->x;
        fwrite ( &float_val, sizeof(float), 1, f );
        float_val = this_mol_instance->y;
        fwrite ( &float_val, sizeof(float), 1, f );
        float_val = this_mol_instance->z;
        fwrite ( &float_val, sizeof(float), 1, f );
        // NOTE: The following equations are from pick_displacement in diffuse.c
        this_mol_instance->x += ds * mcell_random->rng_gauss() * 0.70710678118654752440;
        this_mol_instance->y += ds * mcell_random->rng_gauss() * 0.70710678118654752440;
        this_mol_instance->z += ds * mcell_random->rng_gauss() * 0.70710678118654752440;
        this_mol_instance = this_mol_instance->next;
      }

    }

    fclose(f);

  }
}

